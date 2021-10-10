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
use dbreps2::{str_vec, Frequency, Linker, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_namespace: u32,
    page_title: String,
    birth_year: i32,
    death_year: i32,
}

pub struct UnbelievableLifeSpans {}

#[async_trait::async_trait]
impl Report<Row> for UnbelievableLifeSpans {
    fn title(&self) -> &'static str {
        "Unbelievable life spans"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* unbelievablelifespans.rs SLOW_OK */
SELECT
  page_namespace,
  page_title,
  deathyear
FROM
  (
    SELECT
      page_namespace,
      page_title AS page_title,
      CAST(SUBSTRING_INDEX(cl3.cl_to, '_', 1) AS UNSIGNED) AS deathyear
    FROM
      categorylinks AS cl1
      LEFT JOIN categorylinks AS cl2 ON cl1.cl_from = cl2.cl_from
      AND cl2.cl_to IN ('Longevity_traditions', 'Longevity_claims')
      JOIN categorylinks AS cl3 ON cl1.cl_from = cl3.cl_from
      AND cl3.cl_to REGEXP '^[0-9]+_deaths$'
      JOIN page ON page_id = cl1.cl_from
    WHERE
      cl1.cl_to = CONCAT(?, '_births')
      AND cl2.cl_from IS NULL
  ) AS BornAndDeads
WHERE
  ? > deathyear
  OR deathyear - ? > 122;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let current_year = {
            use chrono::prelude::*;
            Utc::now().year()
        };
        let mut rows = vec![];
        for birth_year in 1..=current_year {
            let year_rows = conn
                .exec_map(
                    self.query(),
                    (birth_year, birth_year, birth_year),
                    |(page_namespace, page_title, death_year)| Row {
                        page_namespace,
                        page_title,
                        birth_year,
                        death_year,
                    },
                )
                .await?;
            rows.extend(year_rows);
        }
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Birth year", "Death year", "Life span"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            Linker::new(row.page_namespace, &row.page_title),
            row.birth_year,
            row.death_year,
            row.death_year - row.birth_year
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("unbelievablelifespans.rs")
    }
}
