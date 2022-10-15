use anyhow::Result;
use clap::Parser;
use dbreps2::Report;

mod enwiki;
mod general;

/// Parsing args, yo
#[derive(Parser, Debug)]
#[clap(author, version, about, long_about = None)]
struct Args {
    /// Report name such as "User categories"
    #[clap(short, long)]
    report: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    match &args.report {
        Some(report) => println!("Only running the \"{}\" report", report),
        None => println!("Running all reports"),
    }

    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();
    /* enwiki reports */
    let enwiki_runner = dbreps2::Runner::new(
        "en.wikipedia.org",
        "enwiki",
        args.report.clone(),
    )
    .await?;
    (general::ArticlesMostRedirects {})
        .really_run(&enwiki_runner)
        .await;
    (general::ExcessiveIps {}).really_run(&enwiki_runner).await;
    (general::ExcessiveUsers {})
        .really_run(&enwiki_runner)
        .await;
    (general::IndefFullRedirects {})
        .really_run(&enwiki_runner)
        .await;
    (general::IndefIPs {}).really_run(&enwiki_runner).await;
    (general::LinkedEmailsInArticles {})
        .really_run(&enwiki_runner)
        .await;
    // Too slow, timing out
    // (general::LinkedRedlinkedCats {}).really_run(&enwiki_runner).await;
    (general::OldEditors {}).really_run(&enwiki_runner).await;
    (general::Pollcats {}).really_run(&enwiki_runner).await;
    (general::UncatCats {}).really_run(&enwiki_runner).await;
    (general::UncatTemps {}).really_run(&enwiki_runner).await;
    (general::UserLinksInArticles {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::BrokenWikiProjTemps {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::ConflictedFiles {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::EmptyCats {}).really_run(&enwiki_runner).await;
    (enwiki::LinkedMiscapitalizations {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::LinkedMisspellings {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::LongStubs {}).really_run(&enwiki_runner).await;
    (enwiki::LotNonFree {}).really_run(&enwiki_runner).await;
    (enwiki::NewProjects {}).really_run(&enwiki_runner).await;
    (enwiki::OldDeletionDiscussions {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::OrphanedAfds {}).really_run(&enwiki_runner).await;
    (enwiki::OrphanedSubTalks {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::OverusedNonFree {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::PollTemps {}).really_run(&enwiki_runner).await;
    (enwiki::Potenshbdps1 {}).really_run(&enwiki_runner).await;
    (enwiki::Potenshbdps3 {}).really_run(&enwiki_runner).await;
    (enwiki::Potenshblps1 {}).really_run(&enwiki_runner).await;
    (enwiki::Potenshblps2 {}).really_run(&enwiki_runner).await;
    (enwiki::Potenshblps3 {}).really_run(&enwiki_runner).await;
    (enwiki::ProjectChanges {}).really_run(&enwiki_runner).await;
    (enwiki::ShortestBios {}).really_run(&enwiki_runner).await;
    (enwiki::StickyProdBLPs {}).really_run(&enwiki_runner).await;
    (enwiki::TemplateDisambigs {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::TemplatesNonFree {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::UnbelievableLifeSpans {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::UncatUnrefBLPs {}).really_run(&enwiki_runner).await;
    (enwiki::UnsourcedBLPs {}).really_run(&enwiki_runner).await;
    (enwiki::UntaggedBLPs {}).really_run(&enwiki_runner).await;
    (enwiki::UntaggedStubs {}).really_run(&enwiki_runner).await;
    (enwiki::UntaggedUnrefBLPs {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::UnusedNonFree {}).really_run(&enwiki_runner).await;
    (enwiki::UnusedTemplates {})
        .really_run(&enwiki_runner)
        .await;
    (enwiki::UserCats {}).really_run(&enwiki_runner).await;

    // Cleanup
    enwiki_runner.pool.disconnect().await?;

    /* commonswiki reports */
    let commonswiki_runner = dbreps2::Runner::new(
        "commons.wikimedia.org",
        "commonswiki",
        args.report.clone(),
    )
    .await?;
    (general::ExcessiveIps {})
        .really_run(&commonswiki_runner)
        .await;

    // Cleanup
    commonswiki_runner.pool.disconnect().await?;

    Ok(())
}
