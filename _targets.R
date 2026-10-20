library(targets)
tar_source()
tar_option_set(packages = c("httr2", "jsonlite", "readr", "dplyr", "tidyr", "stringr", "lubridate"),
               format = "rds", error = "stop")

list(
  tar_target(cms_dataset_id, "yv7e-xc69"),
  tar_target(cms_extract, fetch_cms_dataset(cms_dataset_id), format = "file"),
  tar_target(cms_metadata, cms_extract_metadata(cms_extract)),
  tar_target(cms_current, read_cms_extract(cms_extract)),
  tar_target(cms_schema_check, validate_cms_schema(cms_current), cue = tar_cue(mode = "always")),
  tar_target(hospital_op18_panel, {
    cms_schema_check
    build_hospital_op18_panel(cms_current)
  }),
  tar_target(national_reference_file, "data/raw/Timely_and_Effective_Care-National.csv", format = "file"),
  tar_target(national_reference, read_national_reference(national_reference_file)),
  tar_target(national_op18_summary, summarize_national_op18(national_reference))
)

