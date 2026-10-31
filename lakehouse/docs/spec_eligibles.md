# Spec rules for column names

Column names should have only lower case characters [a-z][0-9] and underscores between words

# Spec for moving into silver table bronze table:
## statewide-medi-cal-certified-eligible-individuals-by-aid-code-2010-to-the-most-recent-reportabl

Grain: month + aid code + delivery system is unique once the 14 flagged rows are excluded (WHERE NOT is_duplicate_placeholder).

| bronze_column        | silver_column | type | cleaning_rule |
|:---------------------|:-------------:|-----:|--------------:|
| Aid Code             |     aid_code      | string | trim              |
| Month of Eligibility |     month_of_eligibility    | date |Append a string '-01', parse as yyyy-MM-dd into date|
|Health Delivery System|health_delivery_system|string|trim|	
Total Eligibles|total_eligibles|int|filter comma out in regexp, parse strings as ints. convert empty values to a null|	
|Annotation Code|annotation_code|string|trim, empty values are null|	
|Annotation Description|annotation_description|string|trim|
|Status|is_provisional|bool|if Status=='P'| 	
|Date of Data|date_of_data|date|if length of string is 9, parse to format from ddMMMyyyy otherwise set to null|	
|NA|row_category|string|See Row Category Spec |
NA|count_status|string|See Count Status Spec|

### Row Category Spec:

```
if aid_code in cleaned_aid_code_set:
    if health_delivery_system in ['Managed Care','Fee-for-Service']:
        row_category='aid_code_detail'
    elif health_delivery_system == 'Total':
        row_category='aid_code_subtotal'
    else
        row_category='aid_code_unknown_rowtype'
elif aid_code=='STATEWIDE':
    row_category='statewide_total'
elif aid_code=='Other Aid Codes Total':
    row_category='other_aid_codes_total'
elif aid_code=='Suppressed Cell Total':
    row_category='suppressed_cells_total'
else
    row_category='unknown'
```
### Count Status Spec:
```
if total_eligibles is not None annotation_code is None:
    count_status = 'reported'
elif annotation_code in ['1','2']:
    count_status = 'suppressed'
else
    count_status = 'missing_unexplained'
```

# Spec for moving into silver table bronze table:
## california-medicaid-eligibility-groups-by-medi-cal-aid-code

Grain: One row per aid code and eligibility group. Aid codes reported to T-MSIS (269) have one row per T-MSIS eligibility group they map to; other aid codes (100) have exactly one row, where eligibility_group holds a non-federal program description or placeholder and the federal classification columns are N/A.

| bronze_column        | silver_column | type | cleaning_rule |
|:---------------------|:-------------:|-----:|--------------:|
| AID CODE|aid_code|string|if length(AID CODE)<2 prepend '0'|
|(others)|lower case and underscore |string|trim and remove newlines|

