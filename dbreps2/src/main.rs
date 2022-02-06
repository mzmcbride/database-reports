use anyhow::Result;
use clap::Parser;
use dbreps2::Report;
use log::{error, info};
use mysql_async::Pool;

mod enwiki;
mod general;

/// Parsing args, yo
#[derive(Parser, Debug)]
#[clap(author, version, about, long_about = None)]
struct Args {
    /// Report name such as "enwiki::UserCats"
    #[clap(short, long)]
    report: Option<String>,
}

macro_rules! run {
    ( $client:expr, $pool:expr, $( $x:expr ),* ) => {
        $(
            let report = $x;
            match report.run($client, $pool).await {
                Ok(_) => {},
                Err(err) => {
                    error!("{}", err.to_string());
                }
            }
        )*
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();
    let mut debug_single_report: bool = false;
    let mut single_report_name = "".to_string();
    match args.report {
        Some(report) => {
            debug_single_report = true;
            single_report_name.replace_range(.., &report);
        },
        None => println!("Running all ze reports..."),
    }

    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();
    let cfg = dbreps2::load_config().await?;
    /* enwiki reports */
    let enwiki_api =
        mwapi::Client::bot_builder("https://en.wikipedia.org/w/api.php")
            .set_botpassword(&cfg.auth.username, &cfg.auth.password)
            .build()
            .await?;
    info!("Setting up MySQL connection pool for enwiki...");
    let enwiki_db = Pool::new(
        toolforge::connection_info!("enwiki", ANALYTICS)?.to_string(),
    );
    if debug_single_report {
        println!("Debugging a single report: {}", single_report_name);
        run!(
            &enwiki_api,
            &enwiki_db,
            single_report_name {}
        );
    } else {
        run!(
            &enwiki_api,
            &enwiki_db,
            /*general::ExcessiveIps {},
            general::ExcessiveUsers {},
            general::IndefFullRedirects {},
            general::IndefIPs {},
            general::LinkedEmailsInArticles {},
            // Too slow, timing out
            // general::LinkedRedlinkedCats {},
            general::OldEditors {},
            general::Pollcats {},
            general::UncatCats {},
            general::UserLinksInArticles {},
            enwiki::BrokenWikiProjTemps {},
            enwiki::ConflictedFiles {},
            enwiki::EmptyCats {},
            enwiki::LinkedMiscapitalizations {},
            enwiki::LinkedMisspellings {},
            enwiki::LongStubs {},
            enwiki::LotNonFree {},
            enwiki::NewProjects {},
            enwiki::OldDeletionDiscussions {},
            enwiki::OrphanedAfds {},
            enwiki::OrphanedSubTalks {},
            enwiki::OverusedNonFree {},
            enwiki::PollTemps {},
            enwiki::Potenshbdps1 {},
            enwiki::Potenshbdps3 {},
            enwiki::Potenshblps1 {},
            enwiki::Potenshblps2 {},
            enwiki::Potenshblps3 {},
            enwiki::ProjectChanges {},
            enwiki::ShortestBios {},
            enwiki::StickyProdBLPs {},
            enwiki::TemplateDisambigs {},
            enwiki::TemplatesNonFree {},
            enwiki::UnbelievableLifeSpans {},
            enwiki::UncatUnrefBLPs {},
            enwiki::UnsourcedBLPs {},
            enwiki::UntaggedBLPs {},
            enwiki::UntaggedStubs {},
            enwiki::UntaggedUnrefBLPs {},
            enwiki::UnusedNonFree {},*/
            enwiki::UserCats {}
        );
    }
    // Cleanup
    enwiki_db.disconnect().await?;

    /* commonswiki reports */
    let commonswiki_api =
        mwapi::Client::bot_builder("https://commons.wikimedia.org/w/api.php")
            .set_botpassword(&cfg.auth.username, &cfg.auth.password)
            .build()
            .await?;
    info!("Setting up MySQL connection pool for commonswiki...");
    let commonswiki_db = Pool::new(
        toolforge::connection_info!("commonswiki", ANALYTICS)?.to_string(),
    );
    run!(&commonswiki_api, &commonswiki_db, general::ExcessiveIps {});
    // Cleanup
    commonswiki_db.disconnect().await?;

    Ok(())
}
