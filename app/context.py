# Context prompts for GA4 dataset

GA4_CONTEXT = """
The dataset is Google Analytics 4 obfuscated sample e-commerce data (bigquery-public-data.ga4_obfuscated_sample_ecommerce).
Tables are partitioned by date using the `TABLE_SUFFIX` suffix, e.g., events_20210101. When querying, restrict the partition with:

    _TABLE_SUFFIX BETWEEN '20210101' AND '20210131'

The column `event_params` is a RECORD / REPEATED field. To unnest values that contain a key/value structure, use UNNEST, e.g.:

```sql
SELECT
  event_name,
  ep.key AS param_key,
  ep.value.string_value AS param_value
FROM
  `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
  UNNEST(event_params) AS ep
WHERE
  _TABLE_SUFFIX BETWEEN '20210101' AND '20210131'
```

Feel free to adapt this structure to the specific query.
"""
