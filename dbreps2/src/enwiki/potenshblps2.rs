/*
Copyright 2012, 2013 bjweeks, MZMcBride, Tim Landscheidt
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
use time::OffsetDateTime;

pub struct Row {
    page_title: String,
    year: i32,
}

pub struct Potenshblps2 {}

#[async_trait::async_trait]
impl Report<Row> for Potenshblps2 {
    fn title(&self) -> &'static str {
        "Potential biographies of living people (2)"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* potenshblps2.rs SLOW_OK */
SELECT
  page_title
FROM
  page
  JOIN categorylinks AS c1 ON c1.cl_from = page_id
  AND c1.cl_to = CONCAT(?, '_births')
  LEFT JOIN categorylinks AS c2 ON c2.cl_from = page_id
  AND (
    c2.cl_to IN (
      'Living_people',
      'Possibly_living_people',
      'Disappeared_people',
      'Missing_people',
      'Year_of_death_unknown',
      'Date_of_death_unknown',
      'Year_of_death_missing',
      'Date_of_death_missing',
      '20th-century_deaths',
      '21st-century_deaths',
      '1900s_deaths',
      '2000s_deaths',
      'People_declared_dead_in_absentia'
    )
    OR c2.cl_to REGEXP '^[0-9]{4}_deaths$'
    OR c2.cl_to REGEXP '^[0-9]{4}_suicides$'
    OR c2.cl_to REGEXP '^[0-9]{3}0s_deaths$'
  )
WHERE
  page_namespace = 0
  AND page_is_redirect = 0
  AND c2.cl_from IS NULL
ORDER BY
  1;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let current_year = OffsetDateTime::now_utc().year();
        let mut rows = vec![];
        for year in 1900..=current_year {
            let year_rows = conn
                .exec_map(self.query(), (year,), |page_title| Row {
                    page_title,
                    year,
                })
                .await?;
            rows.extend(year_rows);
        }
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Articles that are in a \"XXXX births\" category (greater than 1899) \
        that are not in [[:Category:Living people]], [[:Category:Possibly \
        living people]], or a \"XXXX deaths\" category (limited to the first \
        1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography", "Birth year"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title), row.year]
    }

    fn code(&self) -> &'static str {
        include_str!("potenshblps2.rs")
    }
}
