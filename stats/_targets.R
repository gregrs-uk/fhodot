library(targets)
library(tarchetypes)

source("R/functions.R")
con <- DBI::dbConnect(
  RPostgres::Postgres(),
  dbname = "gregrs_fhodot",
  host = "db",
  user = "postgres",
  password = "db"
)

tar_option_set(
  packages = c(
    "colorspace",
    "dbplyr",
    "dplyr",
    "forcats",
    "ggplot2",
    "glue",
    "lubridate",
    "purrr",
    "readr",
    "stringr",
    "tibble",
    "tidyr"
  )
)

list(
  tar_target(ons_districts, fetch_ons_districts(), cue = tar_cue("always")),
  tar_file(bl_districts_file, "data/bl_districts_from_server.csv"),
  tar_target(bl_districts, read_bl_districts(bl_districts_file)),
  tar_target(district_mapping, get_district_mapping(ons_districts, bl_districts)),
  tar_file(old_stats_dir, "data/old-stats"),
  tar_target(old_stats, read_old_stats(old_stats_dir, district_mapping)),
  tar_target(old_stats_osm, get_old_stats_osm(old_stats)),
  tar_target(old_stats_fhrs, get_old_stats_fhrs(old_stats)),
  tar_target(db_stats_osm, fetch_db_stats_osm(), cue = tar_cue("always")),
  tar_target(db_stats_fhrs, fetch_db_stats_fhrs(), cue = tar_cue("always")),
  tar_target(
    stats_by_district,
    get_stats_by_district(
      bind_stats_osm(old_stats_osm, db_stats_osm),
      bind_stats_fhrs(old_stats_fhrs, db_stats_fhrs)
    )
  ),
  tar_target(plots, get_plots_by_district(stats_by_district, ons_districts)),
  tar_file(
    osm_plot_files,
    export_osm_plot(plots, "output"),
    pattern = map(plots)
  ),
  tar_file(
    fhrs_plot_files,
    export_fhrs_plot(plots, "output"),
    pattern = map(plots)
  ),
  tar_render(summary_rmd, "summary.Rmd")
)
