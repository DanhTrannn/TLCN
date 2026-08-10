# Deterministic Vietnamese e-commerce traffic

## Contents

1. Purpose and identity
2. Referential consistency
3. Traffic intensity model
4. Request mix and journeys
5. Reliability behavior
6. Output layout
7. Validation

## 1. Purpose and identity

Generate reproducible access logs for load, BI, DQ, replay, and backfill demonstrations.
Treat all distributions as explicit synthetic assumptions, not observed statistics of a
specific marketplace or the Vietnamese market.

Derive a logical dataset identity from at least:

- scenario ID and generator version;
- seed and UTC anchor time;
- history window and scale;
- timezone and all traffic/campaign distributions;
- referenced OLTP logical identity;
- access-log schema version.

Use independent deterministic random streams for arrivals, journeys, actors, products,
latency, and errors so a small change in one concern does not reshuffle all other data.

## 2. Referential consistency

Generate against the same master identities as the synthetic OLTP dataset:

- authenticated actor keys must resolve to generated customer public IDs;
- product detail/search/cart context must resolve to generated products/variants;
- authenticated traffic must not precede customer creation;
- requests related to a synthetic checkout/order must occur at or before its OLTP
  transaction time within a documented tolerance;
- inactive customers must not generate authenticated business mutations after
  deactivation;
- service, route, method, action, status, and error-code combinations must exist in the
  real web/API contract.

Anonymous requests keep `actor.key = null`. Do not invent stable anonymous identity or
publish anonymous DAU/MAU when clickstream/session identity is outside scope.

## 3. Traffic intensity model

Model request arrivals in `Asia/Ho_Chi_Minh`, then convert timestamps to UTC. Use a
non-homogeneous count model per 15-minute window rather than uniform timestamps:

```text
expected_requests(window)
= base_rate
* day_of_week_factor
* hour_of_day_factor
* seasonal_factor
* campaign_factor
* optional_growth_or_noise
```

Use Poisson counts for ordinary variation or a negative-binomial model when stronger
over-dispersion is intentional. Keep the choice and parameters in configuration.

Recommended scenario behavior:

- normal weekdays have lower daytime demand than evenings;
- Friday/weekend factors may be higher, but remain configurable;
- daily peaks usually occur around lunch and 19:00–23:00 local time;
- Tết has a configured lead/peak/tail window instead of one hard-coded date;
- monthly double-day campaigns cover `1/1`, `2/2`, ..., `12/12` for every year in the
  history window;
- stronger campaign lift may be configured for `9/9`–`12/12` and Black Friday;
- campaign days have bursts at 00:00–02:00, around 12:00, and 20:00–23:00;
- pre-campaign browsing/search/wishlist may rise before checkout/order traffic;
- campaign lift must multiply a baseline rather than replace weekday/hour seasonality.

Avoid exact hard-coded market claims. Name parameters `assumed_*`, document them, and
support sensitivity scenarios such as baseline, campaign-heavy, and failure-spike.

## 4. Request mix and journeys

Generate requests using only real canonical routes. Maintain a configurable mix of:

- storefront/catalog/facet browsing;
- product detail requests;
- normalized safe search and filter requests;
- auth register/login/me/logout;
- wishlist and cart reads/mutations;
- coupon availability and checkout quote;
- checkout submission;
- order history/detail/lifecycle and review;
- lower-volume admin operations;
- health/internal traffic, tagged `system` and excluded from customer traffic marts.

Use latent generator-only journeys to create plausible order, time, and correlation, but
do not emit a session/clickstream identifier unless the active schema explicitly includes
one. A typical latent journey may be:

```text
catalog/search -> product detail -> wishlist/cart -> quote -> checkout -> order detail
```

Journeys may stop at any stage. Keep OLTP as truth for cart abandonment, checkout,
payment, coupon, and order conversion. Access logs describe request demand and outcomes.

Campaigns should alter the mix as well as volume: increase search/product detail before
the event, coupon/quote/cart around campaign start, and checkout/order traffic near the
configured peak. Customer segments may have different campaign affinity, authenticated
coverage, revisit frequency, and product/category preferences.

Use a curated search vocabulary related to generated catalog categories. Normalize it
with the production sanitizer and never synthesize PII-like search values in accepted
records; put deliberate privacy violations only in explicit negative test fixtures.

## 5. Reliability behavior

Generate latency from positive skewed distributions such as log-normal or gamma, with
route-specific baselines. Mutations and checkout may be slower than health/catalog reads.

Generate status/error outcomes conditionally:

- normal 2xx dominates accepted traffic;
- plausible 4xx includes unauthenticated, validation, not found, coupon invalid, stock
  conflict, and invalid state transition;
- controlled 5xx is rare in baseline scenarios;
- load-sensitive latency/error lift may occur during campaign peaks;
- retries get new request IDs and may share trace context only when the generator models
  that behavior explicitly.

Never infer a successful business transaction solely from HTTP 2xx. Correlate with the
generated OLTP record when building validation expectations.

## 6. Output layout

Emit the same compact JSON contract as real producers. Group by fixed UTC half-open
windows and service/instance, sort deterministically by timestamp then request ID, write
JSONL, gzip with deterministic headers, and create an immutable manifest with SHA-256 and
line/time/schema statistics.

Do not append after close. A repeated export of the same logical identity must produce
byte-identical compressed files and manifests except fields explicitly defined as
operational emission metadata; preferably make those deterministic too.

## 7. Validation

Test the following properties rather than checking only total row count:

- identical config produces identical identity and byte output;
- changed distributions produce a different logical identity;
- every line passes the production schema and privacy rules;
- all route/method/action and actor/reference combinations are valid;
- all referenced synthetic actors/products exist at request time;
- timestamps fall in the configured history and correct UTC windows;
- double-day coverage exists for all applicable months/years;
- campaign windows show statistically meaningful configured lift over comparable
  baseline days, including local-time midnight spikes;
- ordinary weekday/hour shapes remain visible outside campaigns;
- request mix, authenticated coverage, error rates, and latency quantiles remain within
  configurable tolerances;
- manifest checksum, byte count, line count, and min/max timestamp are exact;
- replaying generated files does not increase unique Silver requests or Gold KPIs.
