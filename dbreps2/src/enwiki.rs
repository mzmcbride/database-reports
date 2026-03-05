/*
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
mod boteditcount;
mod brokenwikiprojtemps;
mod editcount;
mod featuredbysize;
mod goodarticlesbysize;
mod newprojects;
mod orphanedafds;
mod orphanedsubtalks;
mod potenshbdps4;
mod potenshblps2;
mod projectchanges;
mod stickyprodblps;
mod unbelievablelifespans;
mod untaggedunrefblps;
mod unusedtemplates;
mod unusedtemplatesfiltered;
mod usercats;
mod webhostpages;

pub use {
    boteditcount::BotEditCount, brokenwikiprojtemps::BrokenWikiProjTemps,
    editcount::EditCount, featuredbysize::FeaturedBySize,
    goodarticlesbysize::GoodArticlesBySize, newprojects::NewProjects,
    orphanedafds::OrphanedAfds, orphanedsubtalks::OrphanedSubTalks,
    potenshbdps4::Potenshbdps4, potenshblps2::Potenshblps2,
    projectchanges::ProjectChanges, stickyprodblps::StickyProdBLPs,
    unbelievablelifespans::UnbelievableLifeSpans,
    untaggedunrefblps::UntaggedUnrefBLPs, unusedtemplates::UnusedTemplates,
    unusedtemplatesfiltered::UnusedTemplatesFiltered, usercats::UserCats,
    webhostpages::WebhostPages,
};
