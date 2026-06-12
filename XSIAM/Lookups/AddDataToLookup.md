# Add Data To Lookup Datasets

**Author Name:** Kris Bajkowski  
**Platform:** Cortex XSIAM  

## Description
This automation script manages the ingestion of new data or the updating of existing data within Cortex XSIAM Lookup Datasets. It interacts directly with the XSIAM `/public_api/v1/xql/lookups/add_data` endpoint via the `core-api-post` command. 

The script supports both physical files (CSV, TSV, and JSON) uploaded to the WarRoom and raw JSON payloads passed from playbook tasks. 

**Automatic Data Processing Features:**
* **System Field Scrubbing:** Automatically removes protected XSIAM system fields (`_time` and `_insert_time`) from the payload prior to ingestion to prevent API errors.
* **Schema Enforcement:** Automatically converts integers, floats, and complex nested structures (JSON arrays/dictionaries) into strings. This ensures the payload strictly matches the XSIAM text-based schema requirements while preserving the exact JSON structure for XQL queries.
* **Error Handling:** Automatically parses API responses to provide explicit, readable failure reasons in the WarRoom if the ingestion does not succeed.

---

## Input Arg Requirements

To configure this script properly, set up the following arguments in the script settings:

| Argument | Requirement | Description |
| :--- | :--- | :--- |
| **`dataset_name`** | **Mandatory** | The exact name of the target lookup dataset in XSIAM. |
| **`mode`** | **Mandatory** | Determines how the data is applied. <br>*Predefined values:* `add_new`, `update_existing`. |
| **`input_type`** | **Mandatory** | Specifies the source of the data payload. <br>*Predefined values:* `file`, `raw`. *(Default: `file`)* |
| **`entry_id`** | *Conditional* | The WarRoom Entry ID of the uploaded file. <br>*Note: Mandatory if `input_type` is set to `file`.* |
| **`raw_data`** | *Conditional* | A properly formatted JSON string or array (e.g., `[{"id":"1", "user":"bob"}]`). <br>*Note: Mandatory if `input_type` is set to `raw`.* |
| **`key_fields`** | *Conditional* | A comma-separated list of column headers used to match and overwrite rows (e.g., `hostname,ip_address`). <br>*Note: Mandatory if `mode` is set to `update_existing`.* |

---

## Outputs

The script outputs a summary of the ingestion process directly to the WarRoom and Context Data under the path **`AddDataToLookup.LookupDataset`**.

| Context Key | Description |
| :--- | :--- |
| **`dataset_name`** | The name of the dataset modified. |
| **`added`** | The number of new rows successfully added. |
| **`updated`** | The number of existing rows successfully updated. |
| **`skipped`** | The number of rows skipped during the ingestion process. |
