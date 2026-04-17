# Remote XQL Query & Data Seeder Script | XSIAM

**Author Name:** Kris Bajkowski  
**Platform:** XSIAM  

## Description
This script utilizes the Core REST API Integration within XSIAM to execute an XQL query on a remote production server from a development server. It retrieves the query results, processes the data schema, and generates two specific JSON files:
1. A flattened, masked **seed file** (`seed_file.json`) containing only the first row of data with all values replaced by `"placeholder"`.
2. A complete **data file** (`data.json`) containing the full set of query results.

During data processing, the script automatically drops the `_time` and `_insert_time` columns and strips any leading underscores from the remaining column names. Both generated files are returned directly to the WarRoom/Context Data.

## Prerequisites

**Core REST API Integration Setup:**
To use this script, you must have the **Cortex Core REST API** integration enabled and configured. Specifically, you need an integration instance set up on your development/current environment that is explicitly authenticated and pointed at the **source (production) instance** of XSIAM. 
* The name of this integration instance will be passed into the `source_using` argument to ensure the script routes the API calls to the correct remote server.

## Input Arg Requirements

To use this script properly in XSIAM, you need to provide the following args:

| Argument | Requirement | Description |
| :--- | :--- | :--- |
| **`source_using`** | **Mandatory** | The exact name of the Core REST API integration instance configured to reach out to the production/remote server. |
| **`xql_query`** | **Mandatory** | The exact XQL query string you want to execute on the production system. Provide limits directly within this query if needed. |
| **`time_from`** | **Mandatory** | The start of the timeframe for the query, represented in epoch milliseconds (e.g., `1598907600000`). |
| **`time_to`** | **Mandatory** | The end of the timeframe for the query, represented in epoch milliseconds (e.g., `1599080399000`). |

## Outputs

The script outputs two files directly to the WarRoom as downloadable artifacts and populates Context Data with the file metadata.

* **File 1:** `seed_file.json` 
  * A single-line, flattened JSON object representing the first row of results. All primitive values (strings, ints, booleans) are masked and replaced with the string `"placeholder"`.
* **File 2:** `data.json` 
  * A pretty-printed, bulk JSON array containing all retrieved rows, with system time columns removed and leading underscores stripped from column keys.
