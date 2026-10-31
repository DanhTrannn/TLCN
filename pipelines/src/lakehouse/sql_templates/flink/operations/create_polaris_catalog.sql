CREATE CATALOG {{catalog_name}} WITH (
    'type'                   = 'iceberg',
    'catalog-type'           = 'rest',
    'uri'                    = {{polaris_uri}},
    'credential'             = {{credential}},
    'warehouse'              = {{warehouse}},
    'scope'                  = 'PRINCIPAL_ROLE:ALL',
    'header.Polaris-Realm'   = {{realm}},
    'io-impl'                = 'org.apache.iceberg.aws.s3.S3FileIO',
    's3.endpoint'            = {{minio_endpoint}},
    's3.path-style-access'   = 'true',
    's3.access-key-id'       = {{s3_access_key}},
    's3.secret-access-key'   = {{s3_secret_key}}
)
