/*
Copyright 2008, 2013 bjweeks, MZMcBride, CBM, Tim Landscheidt
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
    category: String,
    length: u32,
}

pub struct EmptyCats {}

#[async_trait::async_trait]
impl Report<Row> for EmptyCats {
    fn title(&self) -> &'static str {
        "Empty categories"
    }

    fn frequency(&self) -> Frequency {
        Frequency::DailyAt(1)
    }

    fn query(&self) -> &'static str {
        r#"
/* emptycats.rs SLOW_OK */
SELECT
  page_title,
  page_len
FROM
  categorylinks
  RIGHT JOIN page ON cl_to = page_title
WHERE
  page_namespace = 14
  AND page_is_redirect = 0
  AND cl_to IS NULL
  AND NOT(
    CONVERT(page_title USING utf8) REGEXP '(-importance|-class|assess|_articles_missing_|_articles_in_need_of_|_articles_undergoing_|_articles_to_be_|_articles_not_yet_|_articles_with_|_articles_without_|_articles_needing_|Wikipedia_featured_topics)'
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      categorylinks
    WHERE
      cl_from = page_id
      AND (
        cl_to = 'Wikipedia_soft_redirected_categories'
        OR cl_to = 'Disambiguation_categories'
        OR cl_to = 'Monthly_clean-up_category_counter'
        OR cl_to LIKE 'Empty_categories%'
      )
  )
  AND NOT EXISTS (
    SELECT
      1
    FROM
      templatelinks
    JOIN linktarget ON tl_target_id = lt_id
    WHERE
      tl_from = page_id
      AND lt_namespace = 10
      AND (
        lt_title = 'Empty_category'
        OR lt_title = 'Possibly_empty_category'
        OR lt_title = 'Monthly_clean-up_category'
        OR lt_title = 'Maintenance_category_autotag'
      )
  );
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(category, length)| Row {
                category,
                length,
            })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Empty categories not in [[:Category:Wikipedia soft redirected \
        categories]], not in [[:Category:Disambiguation categories]], not \
        in [[:Category:Monthly clean-up category counter]], not tagged with \
        {{tl|Maintenance category autotag}}, and not containing \"(-importance\
        |\\-class|assess|articles missing|articles in need of|articles \
        undergoing|articles to be|articles not yet|articles with|articles \
        without|articles needing|Wikipedia featured topics)\""
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category", "Length"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("{{{{clh|1={}}}}}", row.category), row.length]
    }

    fn code(&self) -> &'static str {
        include_str!("emptycats.rs")
    }
}
