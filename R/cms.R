# CMS Provider Data Catalog retrieval helpers.
# Dataset ID is stable; the current distribution can change as CMS refreshes data.

cms_api_base <- "https://data.cms.gov/provider-data/api/1"

fetch_cms_dataset <- function(dataset_id, page_size = 1500L) {
  stopifnot(is.character(dataset_id), length(dataset_id) == 1L)
  dir.create("data/raw", recursive = TRUE, showWarnings = FALSE)
  url <- sprintf("%s/datastore/query/%s/0", cms_api_base, dataset_id)
  offset <- 0L
  pages <- list()
  repeat {
    response <- httr2::request(url) |>
      httr2::req_url_query(size = page_size, offset = offset) |>
      httr2::req_timeout(60) |>
      httr2::req_retry(max_tries = 4) |>
      httr2::req_perform()
    httr2::resp_check_status(response)
    page <- jsonlite::fromJSON(httr2::resp_body_string(response), simplifyVector = FALSE)
    rows <- page$results %||% page$data %||% page
    if (!is.list(rows) || length(rows) == 0L) break
    pages[[length(pages) + 1L]] <- rows
    if (length(rows) < page_size) break
    offset <- offset + page_size
  }
  if (length(pages) == 0L) stop("CMS returned no rows; check the endpoint and response schema.")
  records <- unlist(pages, recursive = FALSE)
  out <- file.path("data/raw", paste0("cms-timely-effective-care-", dataset_id, ".json"))
  jsonlite::write_json(records, out, auto_unbox = TRUE, pretty = FALSE, dataframe = "rows")
  meta <- list(dataset_id = dataset_id, retrieved_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
               source_url = url, row_count = length(records), api_page_size = page_size)
  jsonlite::write_json(meta, sub("\\.json$", "-metadata.json", out), auto_unbox = TRUE, pretty = TRUE)
  out
}

`%||%` <- function(x, y) if (is.null(x)) y else x

cms_extract_metadata <- function(path) {
  jsonlite::read_json(sub("\\.json$", "-metadata.json", path), simplifyVector = TRUE)
}

read_cms_extract <- function(path) {
  rows <- jsonlite::read_json(path, simplifyVector = TRUE)
  as.data.frame(rows, check.names = FALSE, stringsAsFactors = FALSE)
}

validate_cms_schema <- function(data) {
  if (nrow(data) == 0L || ncol(data) == 0L) stop("CMS extract is empty.")
  required <- c("facility_id", "measure_id", "score", "sample", "footnote", "start_date", "end_date")
  missing <- setdiff(required, names(data))
  if (length(missing)) {
    stop("CMS schema changed; missing fields: ", paste(missing, collapse = ", "),
         ". Available fields: ", paste(names(data), collapse = ", "))
  }
  invisible(TRUE)
}

build_hospital_op18_panel <- function(data) {
  validate_cms_schema(data)
  op18 <- data |>
    dplyr::filter(.data$measure_id %in% c("OP_18a", "OP_18b", "OP_18c", "OP_18d")) |>
    dplyr::mutate(
      score_minutes = suppressWarnings(as.numeric(.data$score)),
      sample_n = suppressWarnings(as.integer(.data$sample)),
      start_date = as.Date(.data$start_date, format = "%m/%d/%Y"),
      end_date = as.Date(.data$end_date, format = "%m/%d/%Y")
    ) |>
    dplyr::select(
      facility_id, facility_name, state, countyparish, measure_id, score, score_minutes,
      sample, sample_n, footnote, start_date, end_date
    )
  duplicates <- op18 |>
    dplyr::count(.data$facility_id, .data$measure_id, .data$start_date, .data$end_date) |>
    dplyr::filter(.data$n > 1L)
  if (nrow(duplicates)) stop("Duplicate facility/measure/reporting-period records found; review before reshaping.")
  op18 |>
    tidyr::pivot_wider(
      names_from = measure_id,
      values_from = c(score, score_minutes, sample, sample_n, footnote),
      names_glue = "{.value}_{measure_id}"
    ) |>
    dplyr::mutate(psych_gap_minutes = .data$score_minutes_OP_18c - .data$score_minutes_OP_18b)
}

read_national_reference <- function(path) {
  readr::read_csv(path, show_col_types = FALSE, na = c("", "Not Available", "Not Applicable"))
}

summarize_national_op18 <- function(data) {
  required <- c("Measure ID", "Score", "Footnote", "Start Date", "End Date")
  missing <- setdiff(required, names(data))
  if (length(missing)) stop("National reference is missing columns: ", paste(missing, collapse = ", "))
  selected <- data |>
    dplyr::filter(.data[["Measure ID"]] %in% c("OP_18a", "OP_18b", "OP_18c", "OP_18d")) |>
    dplyr::mutate(score_minutes = suppressWarnings(as.numeric(.data[["Score"]]))) |>
    dplyr::select(measure_id = .data[["Measure ID"]], score_minutes,
                  footnote = .data[["Footnote"]], start_date = .data[["Start Date"]],
                  end_date = .data[["End Date"]])
  psychiatric <- selected$score_minutes[selected$measure_id == "OP_18c"]
  comparator <- selected$score_minutes[selected$measure_id == "OP_18b"]
  if (length(psychiatric) != 1L || length(comparator) != 1L ||
      is.na(psychiatric) || is.na(comparator)) stop("Expected one valid OP_18b and OP_18c national value.")
  list(measures = selected, national_gap_minutes = psychiatric - comparator,
       interpretation = "National reference only; not a hospital benchmark or causal estimate.")
}

