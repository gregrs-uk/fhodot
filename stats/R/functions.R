blue <- "#00CBFF"
red <- "#FF89AC"
green <- "#7ACE00"


fetch_ons_districts <- function() {
  ons_districts <- tbl(con, "la_districts") %>%
    select(code, name_ons = name) %>%
    collect()
}


read_bl_districts <- function(path) {
  read_csv(path) %>%
    select(gid_bl = gid, name_bl = name, code) %>%
    # make manual changes to BoundaryLine codes where districts have amalgamated
    # or codes have been changed
    mutate(
      code = case_when(
        # --- changes in 2019 ---
        # Bournemouth, Christchurch and Poole
        code == "E06000028" ~ "E06000058", # Bournemouth
        code == "E07000048" ~ "E06000058", # Christchurch
        code == "E06000029" ~ "E06000058", # Poole
        # Dorset
        code == "E07000052" ~ "E06000059", # West Dorset
        code == "E07000050" ~ "E06000059", # North Dorset
        code == "E07000049" ~ "E06000059", # East Dorset
        code == "E07000051" ~ "E06000059", # Purbeck
        code == "E07000053" ~ "E06000059", # Weymouth and Portland
        # Somerset West and Taunton, see 2023, when further amalgamated
        # code == "E07000191" ~ "E07000246", # West Somerset
        # code == "E07000190" ~ "E07000246", # Taunton Deane
        # West Suffolk
        code == "E07000201" ~ "E07000245", # Forest Heath
        code == "E07000204" ~ "E07000245", # St Edmundsbury
        # East Suffolk
        code == "E07000206" ~ "E07000244", # Waveney
        code == "E07000205" ~ "E07000244", # Suffolk Coastal
        # --- changes in 2020 ---
        # Buckinghamshire
        code == "E07000004" ~ "E06000060", # Aylesbury Vale
        code == "E07000007" ~ "E06000060", # Wycombe
        code == "E07000005" ~ "E06000060", # Chiltern
        code == "E07000006" ~ "E06000060", # South Bucks
        # --- changes in 2021 ---
        # North Northamptonshire
        code == "E07000150" ~ "E06000061", # Corby
        code == "E07000152" ~ "E06000061", # East Northamptonshire
        code == "E07000153" ~ "E06000061", # Kettering
        code == "E07000156" ~ "E06000061", # Wellingborough
        # West Northamptonshire
        code == "E07000151" ~ "E06000062", # Daventry
        code == "E07000154" ~ "E06000062", # Northampton
        code == "E07000155" ~ "E06000062", # South Northamptonshire
        # --- changes in 2023 ---
        # Cumberland
        code == "E07000026" ~ "E06000063", # Allerdale
        code == "E07000028" ~ "E06000063", # Carlisle
        code == "E07000029" ~ "E06000063", # Copeland
        # Westmorland and Furness
        code == "E07000027" ~ "E06000064", # Barrow-in-Furness
        code == "E07000030" ~ "E06000064", # Eden
        code == "E07000031" ~ "E06000064", # South Lakeland
        # North Yorkshire
        code == "E07000163" ~ "E06000065", # Craven
        code == "E07000164" ~ "E06000065", # Hambleton
        code == "E07000165" ~ "E06000065", # Harrogate
        code == "E07000166" ~ "E06000065", # Richmondshire
        code == "E07000167" ~ "E06000065", # Ryedale
        code == "E07000168" ~ "E06000065", # Scarborough
        code == "E07000169" ~ "E06000065", # Selby
        # Somerset Council
        code == "E07000187" ~ "E06000066", # Mendip
        code == "E07000188" ~ "E06000066", # Sedgemoor
        code == "E07000191" ~ "E06000066", # West Somerset
        code == "E07000190" ~ "E06000066", # Taunton Deane
        code == "E07000189" ~ "E06000066", # South Somerset
        # --- 1:1 changes of code ---
        code == "S12000015" ~ "S12000047", # Fife
        code == "S12000046" ~ "S12000049", # Glasgow
        code == "S12000024" ~ "S12000048", # Perth and Kinross
        code == "S12000044" ~ "S12000050", # North Lanarkshire
        TRUE ~ code
      )
    )
}


get_district_mapping <- function(ons_districts, bl_districts) {
  ons_districts %>%
    left_join(bl_districts, by = "code")
}


read_old_stats <- function(directory, district_mapping) {
  list.files(directory, full.names = TRUE) %>%
    map_dfr(function(path) {
      read_csv(
        path,
        col_types = cols(
          district_id = col_double(),
          district_name = col_character(),
          matched = col_double(),
          OSM_with_postcode = col_double(),
          OSM_no_postcode = col_double(),
          matched_postcode_error = col_double(),
          mismatch = col_double(),
          FHRS_unmatched = col_double(),
          total_OSM = col_double(),
          total_FHRS = col_double(),
          FHRS_matched_pc = col_double(),
          OSM_matched_or_postcode_pc = col_double()
        )
      ) %>%
        mutate(path = path)
    }) %>%
    rename(
      gid_bl = district_id,
      name_bl_stats = district_name
    ) %>%
    mutate(
      date = path %>%
        str_extract("20[0-9]{2}-[0-9]{2}-[0-9]{2}") %>%
        ymd()
    ) %>%
    left_join(district_mapping, by = "gid_bl")
}


get_old_stats_osm <- function(old_stats) {
  old_stats %>%
    mutate(unmatched = OSM_with_postcode + OSM_no_postcode) %>%
    select(
      date,
      district_code = code,
      matched_same_postcodes = matched,
      matched_different_postcodes = matched_postcode_error,
      mismatched = mismatch,
      unmatched
    ) %>%
    pivot_longer(
      cols = c(
        matched_same_postcodes,
        matched_different_postcodes,
        mismatched,
        unmatched
      ),
      names_to = "statistic",
      values_to = "value"
    ) %>%
    group_by(date, district_code, statistic) %>%
    summarise(value = sum(value), .groups = "drop")
}


get_old_stats_fhrs <- function(old_stats) {
  old_stats %>%
    select(
      date,
      district_code = code,
      matched_same_postcodes = matched,
      matched_different_postcodes = matched_postcode_error,
      # old version relied on establishments having a location to be in stats
      unmatched_with_location = FHRS_unmatched
    ) %>%
    pivot_longer(
      cols = c(
        matched_same_postcodes,
        matched_different_postcodes,
        unmatched_with_location
      ),
      names_to = "statistic",
      values_to = "value"
    ) %>%
    group_by(date, district_code, statistic) %>%
    summarise(value = sum(value), .groups = "drop")
}


fetch_db_stats_osm <- function() {
  tbl(con, "stats_osm") %>% collect()
}


fetch_db_stats_fhrs <- function() {
  tbl(con, "stats_fhrs") %>%
    left_join(tbl(con, "fhrs_authorities"), by = c("authority_code" = "code")) %>%
    select(date, district_code, statistic, value) %>%
    filter(!is.na(district_code)) %>%
    collect()
}


bind_stats_osm <- function(old_stats_osm, db_stats_osm) {
  bind_rows(
    old_stats_osm %>%
      filter(date < min(db_stats_osm$date)) %>%
      mutate(old = TRUE),
    db_stats_osm %>%
      mutate(old = FALSE)
  )
}


bind_stats_fhrs <- function(old_stats_fhrs, db_stats_fhrs) {
  bind_rows(
    old_stats_fhrs %>%
      filter(date < min(db_stats_fhrs$date)) %>%
      mutate(old = TRUE),
    db_stats_fhrs %>%
      mutate(old = FALSE)
  )
}


get_stats_by_district <- function(stats_osm, stats_fhrs) {
  bind_rows(
    mutate(stats_osm, type = "osm"),
    mutate(stats_fhrs, type = "fhrs")
  ) %>%
    nest(data = -c(district_code, type)) %>%
    pivot_wider(names_from = type, values_from = data, names_prefix = "stats_")
}


get_osm_plot <- function(data, district_name) {
  osm_statistic_defs <- tribble(
    ~ statistic, ~ label, ~ colour,
    "unmatched", "Unmatched", blue,
    "mismatched", "Invalid fhrs:id", lighten(red, 0.3),
    "matched_different_postcodes", "Matched (different postcodes)", red,
    "matched_same_postcodes", "Matched (same postcodes)", green
  ) %>%
    mutate(label = fct_inorder(label))
  
  data %>%
    left_join(osm_statistic_defs, by = "statistic") %>%
    ggplot(aes(date, value, fill = label)) +
    geom_area() +
    scale_x_date(
      date_breaks = "1 year",
      date_minor_breaks = "1 month",
      labels = year
    ) +
    scale_fill_manual(
      values = osm_statistic_defs %>% select(label, colour) %>% deframe()
    ) +
    guides(fill = guide_legend(reverse = TRUE, nrow = 2)) +
    labs(
      title = glue("Relevant OSM objects in {district_name}"),
      x = "Date",
      y = "Number of relevant OSM objects",
      fill = NULL,
      caption = paste(
        "Relevant OSM objects are those likely to appear in FHRS data plus",
        "those with an fhrs:id tag set"
      )
    ) +
    theme(legend.position = "bottom")
}


get_fhrs_statistic_defs <- function() {
  tribble(
    ~ statistic, ~ label, ~ colour,
    "unmatched_without_location", "Unmatched (without location)", darken(blue, 0.2),
    "unmatched_with_location", "Unmatched (with location)", blue,
    "matched_different_postcodes", "Matched (different postcodes)", red,
    "matched_same_postcodes", "Matched (same postcodes)", green
  ) %>%
    mutate(label = fct_inorder(label))
}


get_fhrs_plot <- function(data, district_name) {
  fhrs_statistic_defs <- get_fhrs_statistic_defs()
  
  data %>%
    left_join(fhrs_statistic_defs, by = "statistic") %>%
    ggplot(aes(date, value, fill = label)) +
    geom_area() +
    scale_x_date(
      date_breaks = "1 year",
      date_minor_breaks = "1 month",
      labels = year
    ) +
    scale_fill_manual(
      values = fhrs_statistic_defs %>% select(label, colour) %>% deframe()
    ) +
    guides(fill = guide_legend(reverse = TRUE, nrow = 2)) +
    labs(
      title = glue("FHRS establishments in {district_name}"),
      x = "Date",
      y = "Number of FHRS establishments",
      fill = NULL,
      caption = paste(
        "Unmatched establishments with no location not included in data from",
        "old version of tool"
      )
    ) +
    theme(legend.position = "bottom")
}


get_plots_by_district <- function(stats_by_district, ons_districts) {
  stats_by_district %>%
    left_join(ons_districts, by = c("district_code" = "code")) %>%
    mutate(
      plot_osm = map2(stats_osm, name_ons, get_osm_plot),
      plot_fhrs = map2(stats_fhrs, name_ons, get_fhrs_plot)
    ) %>%
    select(-starts_with("stats_"))
}


export_plot <- function(plot, path) {
  output_dir <- dirname(path)
  if(!dir.exists(output_dir)) dir.create(output_dir)
  
  ggsave(
    path,
    plot,
    width = 6, height = 4,
    dpi = 150
  )
  
  path # return for targets to track
}


export_osm_plot <- function(row, directory) {
  path <- file.path(directory, paste0("osm-", row$district_code[[1]], ".png"))
  export_plot(row$plot_osm[[1]], path) # returns path
}


export_fhrs_plot <- function(row, directory) {
  path <- file.path(directory, paste0("fhrs-", row$district_code[[1]], ".png"))
  export_plot(row$plot_fhrs[[1]], path) # returns path
}