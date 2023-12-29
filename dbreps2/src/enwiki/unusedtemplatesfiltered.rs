/*
Copyright 2011, 2018 bjweeks, MZMcBride
Copyright 2022 Kunal Mehta <legoktm@debian.org>

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
use dbreps2::{str_vec, y_m_d, Frequency, Report};
use log::debug;
use mysql_async::prelude::*;
use mysql_async::Conn;
use std::collections::HashSet;

const SKIP_SUFFIXES: [&str; 4] =
    ["/testcases", "/sandbox", "/rater-data.js", "-stub"];

const SKIP_PREFIXES: [&str; 13] = [
    "Adminstats/",
    "AfC_",
    "Cite_doi/",
    "Cite_pmid/",
    "Did_you_know_nominations/",
    "Editnotices/",
    "PBB/",
    "POTD_caption/",
    "POTD_credit/",
    "POTD_protected/",
    "TemplateStyles_sandbox/",
    "TFA_title/",
    "User_",
];

/// Returned by the first main query
struct FirstRow {
    page_id: u64,
    page_title: String,
}

/// Returned by the second subquery
struct SecondRow {
    actor_id: u64,
    rev_timestamp: String,
}

pub struct Row {
    template: String,
    first_edit: String,
    latest_edit: String,
    unique_authors: usize,
    revisions: usize,
}

pub struct UnusedTemplatesFiltered {}

impl UnusedTemplatesFiltered {
    fn subquery(&self) -> &'static str {
        r#"
/* unusedtemplatesfiltered.rs */
SELECT
  actor_id,
  rev_timestamp
FROM
  revision_userindex
  JOIN actor ON actor_id = rev_actor
WHERE
  rev_page = ?;
"#
    }
}

impl Report<Row> for UnusedTemplatesFiltered {
    fn title(&self) -> &'static str {
        "Unused templates (filtered)"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Daily
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(4000)
    }

    fn static_row_numbers(&self) -> bool {
        true
    }

    fn query(&self) -> &'static str {
        r#"
/* unusedtemplatesfiltered.rs SLOW_OK */
SELECT
  page_id,
  page_title
FROM
  page
  LEFT JOIN linktarget ON page_namespace = lt_namespace
  AND page_title = lt_title
WHERE
  page_namespace = 10
  AND page_is_redirect = 0
  AND lt_id IS NULL
  AND page_title NOT IN (
    SELECT
      page_title
    FROM
      page
      JOIN categorylinks ON page_id = cl_from
    WHERE
      cl_to IN (
        'Wikipedia_substituted_templates',
        'Wikipedia_transclusionless_templates',
        'Deprecated_templates_kept_for_historical_reasons',
        'Inactive_project_pages',
        'Parameter_shared_content_templates',
        'Computer_language_user_templates',
        'Language_user_templates',
        'Template_test_cases',
        'Template_sandboxes',
        'Level-zero_userbox_templates',
        'Templates_for_deletion'
      )
      AND page_namespace = 10
  )
ORDER BY
  page_title ASC;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let first_rows = conn
            .query_map(self.query(), |(page_id, page_title)| FirstRow {
                page_id,
                page_title,
            })
            .await?;
        let mut rows = vec![];
        let mut stub_rows = vec![];
        for row in first_rows {
            // Filter by page name
            if SKIP_SUFFIXES
                .iter()
                .any(|suffix| row.page_title.ends_with(suffix))
                || SKIP_PREFIXES
                    .iter()
                    .any(|prefix| row.page_title.starts_with(prefix))
            {
                debug!("Skipping {}", row.page_title);
                continue;
            }
            debug!("Running subquery for {}", &row.page_id);
            let second_rows = conn
                .exec_map(
                    self.subquery(),
                    (row.page_id,),
                    |(actor_id, rev_timestamp)| SecondRow {
                        actor_id,
                        rev_timestamp,
                    },
                )
                .await?;
            let mut revisions = 0;
            let mut authors = HashSet::new();
            let mut timestamps = vec![];
            for row in second_rows {
                revisions += 1;
                authors.insert(row.actor_id);
                timestamps.push(row.rev_timestamp);
            }
            timestamps.sort();
            let row = Row {
                template: row.page_title,
                first_edit: timestamps[0].clone(),
                latest_edit: timestamps[timestamps.len() - 1].clone(),
                unique_authors: authors.len(),
                revisions,
            };
            // Split out stub templates
            if row.template.contains("stub") {
                stub_rows.push(row);
            } else {
                rows.push(row);
            }
        }
        // Sort by template name, then merge in the stub templates
        rows.sort_by_key(|row| row.template.clone());
        stub_rows.sort_by_key(|row| row.template.clone());
        rows.extend(stub_rows);
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Unused templates (filtered)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec![
            "Template",
            "First edit",
            "Latest edit",
            "Unique authors",
            "Revisions",
        ]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!(
                "[[:Template:{}|{}]]",
                row.template,
                row.template.replace('_', " ")
            ),
            y_m_d(&row.first_edit),
            y_m_d(&row.latest_edit),
            row.unique_authors,
            row.revisions
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("unusedtemplatesfiltered.rs")
    }
}

#[cfg(test)]
mod tests {

    #[test]
    fn test_no_spaces() {
        let with_spaces: Vec<_> = super::SKIP_PREFIXES
            .into_iter()
            .filter(|p| p.contains(' '))
            .collect();
        assert!(
            with_spaces.is_empty(),
            "Items in SKIP_PREFIXES should use underscores instead of spaces"
        );
        let with_spaces: Vec<_> = super::SKIP_SUFFIXES
            .into_iter()
            .filter(|p| p.contains(' '))
            .collect();
        assert!(
            with_spaces.is_empty(),
            "Items in SKIP_SUFFIXES should use underscores instead of spaces"
        );
    }
}
