use anyhow::Result;
use dbreps2::{str_vec, DbrLink, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    rd_title: String,
    count: u32,
}

pub struct ArticlesMostRedirects {}

#[async_trait::async_trait]
impl Report<Row> for ArticlesMostRedirects {
    fn title(&self) -> &'static str {
        "Articles with the most redirects"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn query(&self) -> &'static str {
        r#"
/* articlesmostredirects.rs SLOW_OK */
SELECT
  rd_title,
  COUNT(*)
FROM
  page
JOIN
  redirect
  ON rd_from = page_id
WHERE
  page_namespace = 0
  AND rd_namespace = 0
GROUP BY rd_namespace, rd_title
ORDER BY COUNT(*) DESC
LIMIT 1500;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(rd_title, count)| Row {
                rd_title,
                count,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Articles with the most redirects \
        (limited to the first 1500 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Article", "Redirects count"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![DbrLink::new(&row.rd_title), row.count]
    }

    fn code(&self) -> &'static str {
        include_str!("articlesmostredirects.rs")
    }
}
