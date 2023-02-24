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
mod conflictedfiles;
mod editcount;
mod emptycats;
mod featuredbysize;
mod linkedmiscapitalizations;
mod linkedmisspellings;
mod longstubs;
mod lotnonfree;
mod newprojects;
mod olddeletiondiscussions;
mod orphanedafds;
mod orphanedsubtalks;
mod overusednonfree;
mod polltemps;
mod potenshbdps1;
mod potenshbdps3;
mod potenshblps1;
mod potenshblps2;
mod potenshblps3;
mod projectchanges;
mod shortestbios;
mod stickyprodblps;
mod templatedisambigs;
mod templatesnonfree;
mod unbelievablelifespans;
mod uncatunrefblps;
mod unsourcedblps;
mod untaggedblps;
mod untaggedstubs;
mod untaggedunrefblps;
mod unusednonfree;
mod unusedtemplates;
mod unusedtemplatesfiltered;
mod usercats;
mod webhostpages;

pub use {
    boteditcount::BotEditCount, brokenwikiprojtemps::BrokenWikiProjTemps,
    conflictedfiles::ConflictedFiles, editcount::EditCount,
    emptycats::EmptyCats, featuredbysize::FeaturedBySize,
    linkedmiscapitalizations::LinkedMiscapitalizations,
    linkedmisspellings::LinkedMisspellings, longstubs::LongStubs,
    lotnonfree::LotNonFree, newprojects::NewProjects,
    olddeletiondiscussions::OldDeletionDiscussions, orphanedafds::OrphanedAfds,
    orphanedsubtalks::OrphanedSubTalks, overusednonfree::OverusedNonFree,
    polltemps::PollTemps, potenshbdps1::Potenshbdps1,
    potenshbdps3::Potenshbdps3, potenshblps1::Potenshblps1,
    potenshblps2::Potenshblps2, potenshblps3::Potenshblps3,
    projectchanges::ProjectChanges, shortestbios::ShortestBios,
    stickyprodblps::StickyProdBLPs, templatedisambigs::TemplateDisambigs,
    templatesnonfree::TemplatesNonFree,
    unbelievablelifespans::UnbelievableLifeSpans,
    uncatunrefblps::UncatUnrefBLPs, unsourcedblps::UnsourcedBLPs,
    untaggedblps::UntaggedBLPs, untaggedstubs::UntaggedStubs,
    untaggedunrefblps::UntaggedUnrefBLPs, unusednonfree::UnusedNonFree,
    unusedtemplates::UnusedTemplates,
    unusedtemplatesfiltered::UnusedTemplatesFiltered, usercats::UserCats,
    webhostpages::WebhostPages,
};
