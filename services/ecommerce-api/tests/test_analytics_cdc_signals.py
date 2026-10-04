"""Tests for CDC real-time operational signal schemas and role metric endpoints."""

from app.modules.analytics.schemas import (
    CashInTransitSignal,
    ChannelPaceComparisonSignal,
    CriticalStockoutSignal,
    DepletionVelocitySignal,
    ExecutiveMetricsResponse,
    FulfillmentBottleneckSignal,
    HourlyMarginPoint,
    HourlyRunRatePoint,
    InventoryMetricsResponse,
    MarginErosionSignal,
    MarketingMetricsResponse,
    NegativeReviewSpikeSignal,
    OperationsMetricsResponse,
    RegionalBoomRateSignal,
    SalesMetricsResponse,
    StoreMetricsResponse,
    StoreRunRateSignal,
    StoreStockoutSignal,
    ViralProductSignal,
    VoucherBurnRateSignal,
)


def test_marketing_metrics_schema_includes_cdc_signals():
    resp = MarketingMetricsResponse(
        role="marketing",
        voucher_burn_rate=VoucherBurnRateSignal(
            coupon_code="SALE50K",
            used_count=850,
            usage_limit=1000,
            burn_rate_per_minute=56.6,
            budget_warning=True,
            budget_burn_percent=85.0,
        ),
        negative_review_spikes=[
            NegativeReviewSpikeSignal(
                product_id=1,
                product_name="Áo Polo Nam",
                negative_count=6,
                window_minutes=45,
                warning_alert="Phát hiện 6 review 1 sao trong 45 phút!",
            )
        ],
    )
    assert resp.voucher_burn_rate is not None
    assert resp.voucher_burn_rate.budget_warning is True
    assert resp.voucher_burn_rate.coupon_code == "SALE50K"
    assert len(resp.negative_review_spikes) == 1
    assert resp.negative_review_spikes[0].negative_count == 6


def test_inventory_metrics_schema_includes_cdc_signals():
    resp = InventoryMetricsResponse(
        role="inventory",
        depletion_velocity=[
            DepletionVelocitySignal(
                variant_id=10,
                sku="POLO-BLK-L",
                product_name="Áo Polo Basic Đen L",
                on_hand=15,
                units_sold_last_hour=60,
                depletion_rate_per_min=1.0,
                estimated_minutes_to_stockout=15,
                alert_level="critical",
            )
        ],
        critical_stockout_alerts=[
            CriticalStockoutSignal(
                variant_id=12,
                sku="JEAN-SLIM-32",
                product_name="Quần Jean Slim 32",
                on_hand=0,
                overselling_prevented=True,
            )
        ],
    )
    assert len(resp.depletion_velocity) == 1
    assert resp.depletion_velocity[0].estimated_minutes_to_stockout == 15
    assert len(resp.critical_stockout_alerts) == 1
    assert resp.critical_stockout_alerts[0].on_hand == 0
    assert resp.critical_stockout_alerts[0].overselling_prevented is True


def test_operations_metrics_schema_includes_cdc_signals():
    resp = OperationsMetricsResponse(
        role="operations",
        regional_boom_rates=[
            RegionalBoomRateSignal(
                region="Bình Tân",
                total_cod_shipments=50,
                failed_cod_shipments=19,
                boom_rate_percent=38.0,
                alert_level="high",
            )
        ],
        fulfillment_bottleneck=FulfillmentBottleneckSignal(
            paid_unfulfilled_orders=250,
            stale_unfulfilled_orders=42,
            bottleneck_warning=True,
            average_waiting_hours=2.5,
        ),
    )
    assert len(resp.regional_boom_rates) == 1
    assert resp.regional_boom_rates[0].boom_rate_percent == 38.0
    assert resp.fulfillment_bottleneck is not None
    assert resp.fulfillment_bottleneck.bottleneck_warning is True


def test_store_metrics_schema_includes_cdc_signals():
    resp = StoreMetricsResponse(
        role="store",
        store_id=1,
        store_stockouts=[
            StoreStockoutSignal(
                variant_id=20,
                sku="JEAN-REG-32",
                product_name="Quần Jean Regular Fit 32",
                on_hand=0,
            )
        ],
        run_rate=StoreRunRateSignal(
            daily_target_vnd=15000000,
            current_revenue_vnd=4200000,
            achievement_percent=28.0,
            projected_revenue_vnd=10500000,
            pace_status="behind",
            hourly_points=[
                HourlyRunRatePoint(hour="10:00", hourly_revenue_vnd=1000000, cumulative_revenue_vnd=1000000, target_vnd=2000000),
                HourlyRunRatePoint(hour="14:00", hourly_revenue_vnd=3200000, cumulative_revenue_vnd=4200000, target_vnd=6000000),
            ],
        ),
    )
    assert len(resp.store_stockouts) == 1
    assert resp.run_rate is not None
    assert resp.run_rate.pace_status == "behind"
    assert len(resp.run_rate.hourly_points) == 2


def test_sales_metrics_schema_includes_cdc_signals():
    resp = SalesMetricsResponse(
        role="sales",
        viral_products=[
            ViralProductSignal(
                product_id=5,
                product_name="Áo Sơ Mi Oxford Màu Be",
                units_sold_recent=48,
                growth_velocity_multiple=8.0,
                viral_badge=True,
            )
        ],
        channel_pace=ChannelPaceComparisonSignal(
            online_growth_percent=180.0,
            store_growth_percent=-40.0,
            dominant_channel="online",
            pace_divergence_warning=True,
        ),
    )
    assert len(resp.viral_products) == 1
    assert resp.viral_products[0].growth_velocity_multiple == 8.0
    assert resp.channel_pace is not None
    assert resp.channel_pace.dominant_channel == "online"


def test_executive_metrics_schema_includes_cdc_signals():
    resp = ExecutiveMetricsResponse(
        role="executive",
        margin_erosion=MarginErosionSignal(
            baseline_margin_percent=52.0,
            current_margin_percent=9.5,
            erosion_drop_percent=42.5,
            erosion_warning=True,
            lowest_margin_hour="14:00",
            hourly_margins=[
                HourlyMarginPoint(hour="09:00", revenue_vnd=100000000, cogs_vnd=48000000, margin_percent=52.0),
                HourlyMarginPoint(hour="14:00", revenue_vnd=300000000, cogs_vnd=271500000, margin_percent=9.5),
            ],
        ),
        cash_in_transit=CashInTransitSignal(
            total_cod_amount_vnd=320000000,
            dispatched_shipments_count=65,
            carrier_breakdown={"GHN": 200000000, "GHTK": 120000000},
        ),
    )
    assert resp.margin_erosion is not None
    assert resp.margin_erosion.erosion_warning is True
    assert len(resp.margin_erosion.hourly_margins) == 2
    assert resp.cash_in_transit is not None
    assert resp.cash_in_transit.total_cod_amount_vnd == 320000000
    assert resp.cash_in_transit.carrier_breakdown["GHN"] == 200000000
