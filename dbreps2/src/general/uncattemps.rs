use anyhow::Result;
use dbreps2::{str_vec, DbrLink, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
}

pub struct UncatTemps {}

#[async_trait::async_trait]
impl Report<Row> for UncatTemps {
    fn title(&self) -> &'static str {
        "Uncategorized templates"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(1000)
    }

    fn query(&self) -> &'static str {
        r#"
/* uncattemps.rs SLOW_OK */
SELECT
  page_title
FROM page
LEFT JOIN categorylinks
ON cl_from = page_id
WHERE page_namespace = 10
AND page_is_redirect = 0
AND ISNULL(cl_from)
AND page_title NOT LIKE '%/%';
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title,)| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Template"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![DbrLink::new(&row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("uncattemps.rs")
    }
}
