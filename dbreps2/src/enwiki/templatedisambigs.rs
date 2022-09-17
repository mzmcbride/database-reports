/*
Copyright 2010, 2013 bjweeks, MZMcBride, Tim Landscheidt
Copyright 2021 Kunal Mehta <legoktm@debian.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

use anyhow::Result;
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    template_title: String,
    disambiguation_title: String,
    transclusions_count: u64,
}

pub struct TemplateDisambigs {}

#[async_trait::async_trait]
impl Report<Row> for TemplateDisambigs {
    fn title(&self) -> &'static str {
        "Templates containing links to disambiguation pages"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* templatedisambigs.rs SLOW_OK */
SELECT
  pltmp.page_title AS template_title,
  pltmp.pl_title AS disambiguation_title,
  (
    SELECT
      COUNT(*)
    FROM
      templatelinks
    WHERE
      tl_namespace = 10
      AND tl_title = pltmp.page_title
  ) AS transclusions_count
FROM
  (
    SELECT
      page_namespace,
      page_title,
      pl_namespace,
      pl_title
    FROM
      page
      JOIN pagelinks ON pl_from = page_id
    WHERE
      page_namespace = 10
      AND pl_namespace = 0
    LIMIT
      1000000
  ) AS pltmp
  JOIN page AS pg2
  /* removes red links */
  ON pltmp.pl_namespace = pg2.page_namespace
  AND pltmp.pl_title = pg2.page_title
WHERE
  EXISTS (
    SELECT
      1
    FROM
      categorylinks
    WHERE
      pg2.page_id = cl_from
      AND cl_to = 'All_disambiguation_pages'
  )
ORDER BY
  transclusions_count DESC;"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(
                    template_title,
                    disambiguation_title,
                    transclusions_count,
                )| Row {
                    template_title,
                    disambiguation_title,
                    transclusions_count,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Templates containing links to disambiguation pages (limited results)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Template", "Disambiguation page", "Transclusions"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("[[Template:{}|]]", row.template_title),
            format!("[[{}]]", row.disambiguation_title),
            row.transclusions_count
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("templatedisambigs.rs")
    }
}
