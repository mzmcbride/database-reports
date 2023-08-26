/*
Copyright 2009, 2013 bjweeks, MZMcBride, Tim Landscheidt
Copyright 2022 Deadbeef <ent3rm4n@gmail.com>
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
use dbreps2::{Frequency, Report};
use mysql_async::{prelude::Queryable, Conn};

pub struct Row {
    namespace: u32,
    title: String,
}

pub struct BlankPages;

#[async_trait::async_trait]
impl Report<Row> for BlankPages {
    fn title(&self) -> &'static str {
        "Blank single-author pages"
    }

    fn query(&self) -> &'static str {
        "
        SELECT
          page_namespace,
          page_title
        FROM page
        WHERE page_len = 0
        AND page_namespace <> 8
        AND (page_namespace NOT IN (2, 3) OR page_title RLIKE '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        AND (SELECT
               COUNT(DISTINCT rev_actor)
             FROM revision_userindex
             WHERE rev_page = page_id) = 1
        LIMIT 1000;
        "
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        Ok(conn
            .query_map(self.query(), |(namespace, title)| Row {
                namespace,
                title,
            })
            .await?)
    }

    fn format_row(&self, Row { namespace, title }: &Row) -> Vec<String> {
        vec![match namespace {
            0 => format!("{{{{plh|1={title}}}}}"),
            _ => format!("{{{{plh|1={{{{subst:ns:{namespace}}}}}:{title}}}}}"),
        }]
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page"]
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn code(&self) -> &'static str {
        include_str!("blankpages.rs")
    }
}
