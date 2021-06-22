use anyhow::Result;
use dbreps2::Report;

mod general;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();
    let cfg = dbreps2::load_config().await?;
    let client =
        mwapi::Client::bot_builder("https://en.wikipedia.org/w/api.php")
            .set_botpassword(&cfg.auth.username, &cfg.auth.password)
            .build()
            .await?;
    // Reports to run
    let report = general::uncatcats::UncatCats {};
    report.run(&client).await?;
    let report = general::indeffullredirects::IndefFullRedirects {};
    report.run(&client).await?;
    Ok(())
}
