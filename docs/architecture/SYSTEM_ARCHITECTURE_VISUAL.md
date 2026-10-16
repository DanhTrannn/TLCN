# System Architecture — Visual View

Tài liệu này trình bày kiến trúc triển khai hiện tại của D&K E-Commerce Data Platform. Phần ML không nằm trong phạm vi kiến trúc đang vận hành.

## 1. System context

```mermaid
flowchart LR
    customer["Khách hàng"]
    operator["Nhân viên cửa hàng<br/>Quản trị viên"]
    analyst["Quản lý và<br/>Data Analyst"]

    platform["D&K E-Commerce<br/>Data Platform"]
    carrier["Nhân viên giao hàng"]

    customer -->|Mua hàng, theo dõi đơn| platform
    operator -->|POS, quản trị, vận hành| platform
    analyst -->|Dashboard và SQL analytics| platform
    carrier -->|Cập nhật giao hàng| platform
```

## 2. Container architecture

```mermaid
flowchart TB
    classDef actor fill:#f8fafc,stroke:#475569,color:#0f172a
    classDef app fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef oltp fill:#fef3c7,stroke:#d97706,color:#451a03
    classDef stream fill:#fce7f3,stroke:#db2777,color:#500724
    classDef lake fill:#dcfce7,stroke:#16a34a,color:#052e16
    classDef query fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef control fill:#e2e8f0,stroke:#64748b,color:#0f172a

    users["Customer / Staff / Admin"]:::actor

    subgraph presentation["Presentation"]
        web["Next.js 15 + React 19<br/>Storefront · POS · Admin BI Hub<br/>:3000"]:::app
        charts["Apache ECharts<br/>Role-based visual analytics"]:::app
    end

    subgraph application["Application and OLTP"]
        api["FastAPI + SQLAlchemy<br/>Auth · RBAC · Business modules<br/>:8000"]:::app
        mysql[("MySQL 8.4<br/>28 OLTP tables")]:::oltp
    end

    subgraph realtime["Streaming path"]
        kafka["Kafka<br/>ecommerce.access_logs"]:::stream
        flink["Flink 1.19<br/>Continuous processing"]:::stream
    end

    subgraph batch["Batch path"]
        airflow["Airflow 2.10<br/>Scheduling and orchestration"]:::control
        spark["Spark 3.5<br/>Extract · DQ · Transform · Commit"]:::lake
    end

    subgraph lakehouse["Lakehouse"]
        minio[("MinIO S3<br/>Parquet + Iceberg data files")]:::lake
        landing["Landing<br/>Raw immutable input"]:::lake
        bronze["Bronze<br/>Source-aligned history"]:::lake
        silver["Silver<br/>Typed · deduplicated · PII protected"]:::lake
        quarantine["Quarantine<br/>Invalid records"]:::control
        gold["Gold<br/>Dimensions · facts · marts"]:::lake
        polaris["Polaris REST Catalog<br/>Iceberg metadata + RBAC"]:::control
    end

    subgraph serving["Analytics serving"]
        trino["Trino 483<br/>Distributed SQL :8084"]:::query
        sqlui["LibreDB Studio<br/>SQL IDE :3001"]:::query
    end

    users -->|HTTPS / JSON| web
    web -->|REST + secure cookies + CSRF| api
    web --- charts
    api -->|Short ACID transactions| mysql
    api -->|Structured access events| kafka

    mysql -->|Read-only incremental extract<br/>27 of 28 tables| spark
    airflow -->|Submit and monitor jobs| spark
    spark --> landing
    kafka --> flink
    flink -->|Streaming Iceberg writes| landing
    landing --> bronze --> silver --> gold
    silver -->|Rejected records| quarantine
    spark -->|Data and manifest files| minio
    flink -->|Data and manifest files| minio
    spark -.->|Catalog commits| polaris
    flink -.->|Catalog commits| polaris
    polaris -.->|Metadata points to| minio

    api -->|Historical metrics| trino
    api -->|Fresh operational signals| mysql
    trino -.->|Resolve tables| polaris
    trino -->|Read Iceberg files| minio
    sqlui --> trino
    sqlui -.->|Operational inspection| mysql
    api -->|RBAC-filtered metrics| charts
```

### Ranh giới trách nhiệm

| Khối | Nguồn dữ liệu chính | Trách nhiệm | Không chịu trách nhiệm |
|---|---|---|---|
| Next.js | FastAPI | UI khách hàng, POS, admin, biểu đồ | Truy cập DB/Trino trực tiếp |
| FastAPI | MySQL, Trino | Nghiệp vụ, auth/RBAC, API analytics | Batch ETL, lưu trữ lịch sử phân tích |
| MySQL | Giao dịch ứng dụng | OLTP và invariant nghiệp vụ | Truy vấn phân tích lịch sử nặng |
| Kafka + Flink | Access events | Luồng log gần thời gian thực | Điều phối batch OLTP |
| Airflow + Spark | MySQL, Landing | Điều phối và xử lý Medallion batch | Phục vụ request người dùng |
| MinIO + Iceberg + Polaris | Data/metadata lakehouse | Lưu file, table format và catalog | Thực thi SQL phân tán |
| Trino | Iceberg Gold | Truy vấn phân tích | Ghi giao dịch OLTP |

## 3. Hai đường đưa dữ liệu vào Lakehouse

```mermaid
flowchart LR
    classDef source fill:#fef3c7,stroke:#d97706
    classDef process fill:#dbeafe,stroke:#2563eb
    classDef layer fill:#dcfce7,stroke:#16a34a
    classDef serving fill:#ede9fe,stroke:#7c3aed

    subgraph batchPath["Batch OLTP — scheduled"]
        mysql[("MySQL<br/>27 analytical tables")]:::source
        extract["Incremental extract<br/>(cursor, primary key)"]:::process
        manifest["Parquet + cryptographic manifest"]:::process
        bLanding["S3 Landing"]:::layer
        bBronze["Iceberg Bronze"]:::layer
        bSilver["Iceberg Silver<br/>MERGE + pseudonymization"]:::layer
        bGold["Iceberg Gold<br/>6 dims · 5 facts · marts"]:::layer
        mysql --> extract --> manifest --> bLanding --> bBronze --> bSilver --> bGold
    end

    subgraph streamPath["Access logs — continuous"]
        api["FastAPI access-log middleware"]:::source
        kafka["Kafka topic"]:::process
        flink["Flink checkpointed job"]:::process
        sLanding["Landing access_logs"]:::layer
        sBronze["Bronze web_events"]:::layer
        sSilver["Silver logs"]:::layer
        sGold["Gold web facts"]:::layer
        api --> kafka --> flink --> sLanding --> sBronze --> sSilver --> sGold
    end

    bGold --> trino["Trino"]:::serving
    sGold --> trino
    trino --> dashboards["FastAPI analytics API<br/>→ ECharts dashboards"]:::serving
```

`customer_credentials` là bảng duy nhất bị loại khỏi batch extraction; dữ liệu xác thực không đi vào Lakehouse.

## 4. Luồng request quan trọng

### 4.1. Giao dịch mua hàng/POS

```mermaid
sequenceDiagram
    autonumber
    actor U as Customer / Staff
    participant W as Next.js
    participant A as FastAPI
    participant D as MySQL
    participant K as Kafka

    U->>W: Thao tác mua hàng hoặc POS
    W->>A: REST request + session + CSRF
    A->>A: Auth, RBAC, validate nghiệp vụ
    A->>D: Short ACID transaction
    D-->>A: Commit / rollback
    A-->>W: JSON response
    W-->>U: Cập nhật UI
    A-->>K: Access event bất đồng bộ
```

### 4.2. Dashboard quản trị

```mermaid
sequenceDiagram
    autonumber
    actor M as Manager
    participant W as Admin BI Hub
    participant A as FastAPI Analytics
    participant T as Trino
    participant G as Iceberg Gold
    participant D as MySQL OLTP

    M->>W: Mở dashboard theo vai trò
    W->>A: GET metrics
    A->>A: Xác thực vai trò và store scope
    A->>T: SQL historical metrics
    T->>G: Scan dimensions, facts, marts
    G-->>T: Analytical result
    T-->>A: Aggregated rows
    opt Chỉ số vận hành cần độ tươi cao
        A->>D: Bounded OLTP query
        D-->>A: Intra-day signals
    end
    A-->>W: RBAC-filtered response
    W-->>M: ECharts visualization
```

## 5. Deployment profiles

```mermaid
flowchart LR
    core["core"] --> coreSvc["Storefront<br/>FastAPI<br/>MySQL<br/>MinIO"]
    batch["batch"] --> batchSvc["Airflow<br/>Spark<br/>Polaris<br/>Trino<br/>PostgreSQL"]
    streaming["streaming"] --> streamSvc["Kafka<br/>Flink<br/>Polaris<br/>MinIO"]
    tools["lakehouse-tools"] --> toolSvc["Spark client<br/>ad-hoc verification"]
```

Các profile dùng chung `lakehouse-network`; PostgreSQL chỉ lưu metadata cho Polaris và Airflow, không chứa dữ liệu nghiệp vụ.

## 6. Quyết định kiến trúc cốt lõi

1. Giao dịch đi qua FastAPI và MySQL; không ghi thẳng vào Lakehouse.
2. Dashboard đi qua FastAPI để giữ RBAC và store-level filtering ở phía server.
3. Trino phục vụ số liệu lịch sử từ Gold; MySQL chỉ bổ sung tín hiệu vận hành cần độ tươi cao.
4. Spark là batch writer; Flink là streaming writer; cả hai commit Iceberg qua Polaris.
5. MinIO giữ data files, Polaris giữ metadata catalog, Trino chỉ thực thi truy vấn.
6. ML là pha tương lai và không nằm trên critical path của hệ thống hiện tại.
