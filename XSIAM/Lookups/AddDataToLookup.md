# Add Data To Lookup Datasets

**Author Name:** Kris Bajkowski  
**Platform:** XSIAM  

## Description
This automation script allows users to ingest new data or update existing data within Cortex XSIAM Lookup Datasets. The script supports processing physical files (CSV, TSV, and JSON) uploaded to the WarRoom, as well as accepting raw JSON payloads passed from playbook tasks. 

It uses the `core-api-post` command to interact with the XSIAM `/public_api/v1/xql/lookups/add_data` endpoint. The script automatically parses API responses to provide explicit failure reasons if the ingestion does not succeed.

## Input Arg Requirements

To configure this script properly in XSIAM, set up the following arguments in the script settings:

| Argument | Requirement | Description |
| :--- | :--- | :--- |
| **`dataset_name`** | **Mandatory** | The exact name of the target lookup dataset in XSIAM. |
| **`mode`** | **Mandatory** | Determines how the data is applied. <br>*Predefined values:* `add_new`, `update_existing`. |
| **`input_type`** | **Mandatory** | Specifies the source of the data payload. <br>*Predefined values:* `file`, `raw`. *(Default: `file`)* |
| **`entry_id`** | *Conditional* | The WarRoom Entry ID of the uploaded file. <br>*Note: Mandatory if `input_type` is set to `file`.* |
| **`raw_data`** | *Conditional* | A properly formatted JSON string or array (e.g., `[{"id":"1", "user":"bob"}]`). <br>*Note: Mandatory if `input_type` is set to `raw`.* |
| **`key_fields`** | *Conditional* | A comma-separated list of column headers used to match and overwrite rows (e.g., `hostname,ip_address`). <br>*Note: Mandatory if `mode` is set to `update_existing`.* |

## Outputs

The script outputs a summary of the ingestion process directly to the WarRoom and Context Data.

* **Context Path:** `AddDataToLookup.LookupDataset`
* **Context Keys:**
    * `dataset_name`: The name of the dataset modified.
    * `added`: The number of new rows successfully added.
    * `updated`: The number of existing rows successfully updated.
    * `skipped`: The number of rows skipped during the ingestion process.
