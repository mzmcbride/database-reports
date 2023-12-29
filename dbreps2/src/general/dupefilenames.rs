// released under public domain; MZMcBride, Tim Landscheidt, Deadbeef; 2011, 2013, 2023

use anyhow::Result;
use dbreps2::{Frequency, Report};
use mysql_async::prelude::Queryable;
use mysql_async::Conn;

pub struct DupeFileNames;

pub struct Row {
    norm_name: String,
    count: usize,
    orig_names_str: String,
}

impl Report<Row> for DupeFileNames {
    fn title(&self) -> &'static str {
        "Largely duplicative file names"
    }

    fn intro(&self) -> &'static str {
        "Largely duplicative file names (limited to the first 1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Normalized name", "Count", "Real names"]
    }

    fn frequency(&self) -> Frequency {
        Frequency::Daily
    }

    fn query(&self) -> &'static str {
        "
        /* dupefilenames.py SLOW_OK */
        SELECT
          LOWER(CONVERT(page_title USING utf8mb4)),
          GROUP_CONCAT(CONVERT(page_title USING utf8mb4) SEPARATOR '|'),
          COUNT(*)
        FROM page
        WHERE page_namespace = 6
        AND page_is_redirect = 0
        GROUP BY 1
        HAVING COUNT(*) > 1
        LIMIT 1000;
        "
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        Ok(conn
            .query_map(self.query(), |(norm_name, orig_names_str, count)| Row {
                norm_name,
                count,
                orig_names_str,
            })
            .await?)
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        vec![
            row.norm_name.clone(),
            row.count.to_string(),
            row.orig_names_str
                .split('|')
                .map(|x| format!("[[:File:{x}|{x}]]"))
                .collect::<Vec<_>>()
                .join(", "),
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("dupefilenames.rs")
    }
}
