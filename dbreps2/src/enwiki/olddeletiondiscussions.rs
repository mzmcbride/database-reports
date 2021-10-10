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
use dbreps2::{str_vec, Frequency, Linker, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_namespace: u32,
    page_title: String,
    cl_timestamp: String,
    cl_to: String,
}

pub struct OldDeletionDiscussions {}

#[async_trait::async_trait]
impl Report<Row> for OldDeletionDiscussions {
    fn title(&self) -> &'static str {
        "Old deletion discussions"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* olddeletiondiscussions.rs SLOW_OK */
SELECT
  page_namespace,
  page_title,
  cl_timestamp,
  cl_to
FROM
  page
  JOIN categorylinks ON cl_from = page_id
WHERE
  cl_to IN (
    'Articles_for_deletion',
    'Templates_for_deletion',
    'Wikipedia_files_for_deletion',
    'Categories_for_deletion',
    'Categories_for_merging',
    'Categories_for_renaming',
    'Redirects_for_discussion',
    'Miscellaneous_pages_for_deletion',
    'Stub_categories_for_deletion',
    'Stub_template_deletion_candidates'
  )
  AND cl_timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY)
  AND NOT(
    page_namespace <> 0
    AND cl_to = 'Articles_for_deletion'
  )
ORDER BY
  page_namespace,
  page_title ASC;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(page_namespace, page_title, cl_timestamp, cl_to)| Row {
                    page_namespace,
                    page_title,
                    cl_timestamp,
                    cl_to,
                },
            )
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Timestamp", "Category"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            Linker::new(row.page_namespace, &row.page_title),
            row.cl_timestamp,
            row.cl_to
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("olddeletiondiscussions.rs")
    }
}
