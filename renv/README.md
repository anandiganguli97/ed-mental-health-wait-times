# renv setup

R is not installed in the build environment, so `renv.lock` has not yet been generated. On a machine with R installed, run:

```r
install.packages("renv")
renv::init(bare = TRUE)
renv::install(c("targets", "httr2", "jsonlite", "readr", "dplyr", "stringr", "lubridate", "quarto"))
renv::snapshot()
```

Commit the resulting lockfile. Later contributors should run `renv::restore()` before building targets.
