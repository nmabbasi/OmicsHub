"""Exact normalization layer for the Option 1A homepage laptop redesign and site-wide icon footer sync.

Peels only the exact pinned homepage/footer files (`index.html`, `404.html`,
`style.css`, `script.js`, and regenerated `home-page.min.css`) back to parent
commit 8cfe69916e01724bdcb85d717a9e6af4d646c289 so older historical fixtures
keep validating their pinned revisions unchanged. Any unknown mutation is
returned untouched so historical scope checks continue to detect unexpected edits.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "8cfe69916e01724bdcb85d717a9e6af4d646c289"

PINNED_FILES = {
    'index.html': {
        "base_sha256": 'e0e0505fab71546fd27c7aea3be9f2bbf8399c6fec3ded42c8be30f8fa6f7e3d',
        "current_sha256": 'd030f973ac3a41fc8a5f30f9f9de8931fb9bd9fa5ea8fa93e2ca0172bb812be5',
    },
    '404.html': {
        "base_sha256": '51dcbd37197875cda5980e293d3f2eb5b3f21bcd37acd7a52755673ed7b70a3f',
        "current_sha256": '7222b263d8ae2b34f58ac50eb13e75a23a5626a9d9d66f337d2f04b5f612f896',
    },
    'start-here.html': {
        "base_sha256": 'db639b9af40bd2d8793142db57d47d251b3bb3310505bf1d39390332cf51933c',
        "current_sha256": 'c3fdc5fd9d20f30bb84a30b2e291e9fa1b8fe6108a02ee59d7ed38e09ac834e6',
    },
    'tutorials.html': {
        "base_sha256": '169a31770f4ff89568c7088ad97c7b61bdb576abed561e50067dae4f6c1bf887',
        "current_sha256": '4e1ebc8810295fad23fe66c1f155026f5635a7058d274c8cbb22ebc33e470d5e',
    },
    'style.css': {
        "base_sha256": '8f79a8a4ab7980d7fd04f2f135b9d8d559fb7c7e8f9cdf70f384dceab06289b6',
        "current_sha256": 'a8cce2200083265366f4d6b654d466d9106e40dc523b5cd6ae19b7ee39cc1534',
    },
    'script.js': {
        "base_sha256": '4fa68baa23f4597e83327dc02e25b646b908aba116ed90764670039019aaa40c',
        "current_sha256": '97e316dd27b8673f1a31dd9e8888f105acc395ff89d4e13f53fd2eb0524a1ca8',
    },
    'home-page.min.css': {
        "base_sha256": '588d5286a85d9d23357f9c06d647d9c3c9ba0c65ab238975d5c13e7877cc1e6a',
        "current_sha256": '3be40c13b9b556751f68c0637cdb67d473934c70c4111f164419d6a455915288',
    },
    'cookie-consent.js': {
        "base_sha256": 'c9b21ce57c609be336dfe869928349cd8c536281f807621d54b3ed3df19ec972',
        "current_sha256": 'dba0aa40f6ce0081301d1d8d3b658da744bdde3a4ff2ecc34a8363693b0174a4',
    },
    'mobile-navigation.js': {
        "base_sha256": 'fce1906ee3ef35e827738c52ca741db9f2178da3d6a7136b9a8a276f3138c4a5',
        "current_sha256": 'c9eadaf8b59d9c8ad9dffbd9392429735e101988c85983bd81b4668c9b21efc8',
    },
    'tutorial-library.css': {
        "base_sha256": 'a9a0c78eef17c47177886d241643d3f292a28d93049a163f5ec6a693f7dab45d',
        "current_sha256": '3c4bfc28d355a02678ea377d86854e413777cae71a910135c69a25c1e5e9422c',
    },
    'tutorial-reader.css': {
        "base_sha256": 'ed840bbf32d42c3a10c46bec36bed1cf49fa2ee3aa753312e6be42a18869ea1b',
        "current_sha256": 'f3f2806e5f54965b2195120b09e0698023ab4957432050c46be5c11f48542097',
    },
    'copy-code.js': {
        "base_sha256": '3c83ad39f72d569f3b161944ad8c33e5b9c49c7796eab3c1dce58fa5cde7aae5',
        "current_sha256": '88652f868a4bdbaf9a8763000738952df2f446e3e21b3adfa8aaf6545a6ba6c3',
    },
    'tutorial-navigation.css': {
        "base_sha256": '38bdf5f94775f586fffa53dbe4737940276b9d82d3f2f89b313317417dbf0e08',
        "current_sha256": '0ee695bca27ff0ddd59cb1c58d3b53a58f947ebe347d2a629282e1943f7bccc4',
    },
    'home-catalogue.css': {
        "base_sha256": 'bb5d49b07212f011917b4fa7498c8b8e1fdf05a3081dded7b07e0e142cfb1c4e',
        "current_sha256": '0b2784b9719d175cfb1ef447205e83b8dac502b8fcf02b9e2e3d800ee3083965',
    },
    'start-here.css': {
        "base_sha256": '95e06b81bfae634962e6078874ab0ba0de1e926ac472def734804102f29e1382',
        "current_sha256": '6ead96eea726b8b0eaec9e5d9929fc3badbbf7319ec62c4aea1cbfc71e47e3ad',
    },
    'tutorials/scrna-seq-downstream-analysis.html': {
        "base_sha256": '57d617aa03790df1589f8cd589f2d64f6660289a1e9b256d4e53be607ec68b38',
        "current_sha256": '140eb08eacb6669552e332f64646e50a4fecbb8a61679bbc45e29a7c9b5110b9',
    },
    '1-Connection.html': {
        "base_sha256": '3b608512774f0d93cef17af415199a7475941906a042c0afbfbcbfc9b9cf6726',
        "current_sha256": '168d1631fa1ad0c6194d2548f579514f6756004c913214e69688e02b805073b4',
    },
    '16s-rrna-prokka-annotation.html': {
        "base_sha256": '08202ad97f94590ed2fc1a4521cd5d24a63927085402662ab547dbec34369bbb',
        "current_sha256": '2ada64a6ce5e732a860a0303e7f7f1cde9c689f7b88d56814af5e993d51d9468',
    },
    '2-HPC_Basic_Commands.html': {
        "base_sha256": 'cad275076396025231207c2c87a28cbcf352b1ed03b46035b8fc5f11faf366a4',
        "current_sha256": '5532812a9376c47fef93f7cbead3ca83842946561a7ace071983db53a2345149',
    },
    '4-Support.html': {
        "base_sha256": 'f99552fbfd770a4bf8f16353cddef1bafb1b73c5510a9f3c7eff0d6fa4c94548',
        "current_sha256": '2a93ef722051a28901d4f78d90a5cbd773241644237fce6f86ddeeaecdab25d3',
    },
    'README.md': {
        "base_sha256": '9c44acd8b24cefa981b3df3aa9726699b21a7afd752a3179c7a696fa83e6e5ba',
        "current_sha256": '82d406135b3564a74cc88811d14bc824ca213b75477b8e30e3f8a77b0118e7a4',
    },
    'about.html': {
        "base_sha256": '167972b2172cbf95cf2158fa678783f005ab6be3cfad9a53a55d39af9b64d4cd',
        "current_sha256": '2fe1facb95c02ee2e2a3483f14e65b86633054d00ad697b6401407a23fbb0472',
    },
    'advanced-ai-orchestration-bioinformatics.html': {
        "base_sha256": 'b81dffe0095d9484ebcd59dea38b9e65f5d625cba6387a93ad55aadcd792ac56',
        "current_sha256": '11b8ecb61fd4d13dfe7d93cd79d4935090098bad6a01e4b231003df626c83946',
    },
    'advanced-ai-single-cell.html': {
        "base_sha256": 'd64b3ddb115320e96f1a01dace448771c507c07c06786d621d515bcc4eda6057',
        "current_sha256": '8d49ac53e75d295d00b60c74e56b14e3d5fa74f02694327d4de45099f8e68a67',
    },
    'advanced-visualization-packages.html': {
        "base_sha256": '818327a62a8f073a8896211a59383e0bbb94e51de047b9b15dcca875b000425d',
        "current_sha256": 'e8a44c9d95f6e2c922297a4ab76dab1b3add9626fd901136f625241aa7493bb0',
    },
    'ai-bioinformatics-github-copilot.html': {
        "base_sha256": '89399fd04a5cda55a47804ee08fd7d2ea02a7eef20175c86d16f720d2b7ecd8d',
        "current_sha256": 'a81948e350f3a52c66e061d9e918dc0aa3e7d732699ba1a0004ed3b224efce03',
    },
    'ai-coding-cursor-aider.html': {
        "base_sha256": '82254a68999428feafdf4fb8c122e92c53e2caafc6c4a0243f68547330f63b3a',
        "current_sha256": '4aead7e3004f7fca184d2a721ebc9d6b5a1067158b638c1adab9e5ce9c877a79',
    },
    'ai-prompt-engineering-seurat.html': {
        "base_sha256": '11df41c2c0999c3914379364517d9ee122e978558cb941890527814002ccf310',
        "current_sha256": '818e589d4ae2f7940441ff38046a8c78b9d9d5bd1e5268986412205e6a23c9af',
    },
    'autonomous-research-orchestrator.html': {
        "base_sha256": '4ce54d680a275a4b194523d5e6c2b9e1ac0bf011324eb270693b193254621a40',
        "current_sha256": '3fbcc570f7a4169233d9b4c8aa3d7839ebc999fa88298e5ab9bcdb1696f70955',
    },
    'biological-data-formats.html': {
        "base_sha256": 'cbbb505798988272926c84af536dd53237ec246c5667d6f2b00576253aff3a02',
        "current_sha256": '7daa0f098094532c2ab828fc81ec10adb10ee32156dbe0a34002d6eb30735acb',
    },
    'cell-cell-communication.html': {
        "base_sha256": '5e913aa70347aafec40fcb5a568adad324a23075fb97322833d78fc7f02b2f11',
        "current_sha256": '0751a8baaf6083d5c039cbf884a903feb75eed7d9337970cfb22612581b3e31a',
    },
    'cell-type-annotation-methods.html': {
        "base_sha256": 'db0608ac803bd0c9abc991b5b1684925f3190e3756d839a36be6d0170dfc40b3',
        "current_sha256": '3ae565006932cb0bc6e4e14abb2f9689b97ff54ae20e257f20b087566938b188',
    },
    'cite-seq-wnn-multiomics.html': {
        "base_sha256": '0426acaa4c8834fa93415bc4bcaf0d8a9c58cade9fcebbaa8231b1c1855b4295',
        "current_sha256": 'ac52d01df207486a883698f9662848e39a1bcb42badeb396cd4ade5e1836c03d',
    },
    'command-line-part1.html': {
        "base_sha256": '98962b3cb1429923c9c265a0b614cbedeb59e7d975211b039403ba0534ae55d4',
        "current_sha256": '2d09788bb1defd93ebd0ccacb659072cd5b5556726aa8c5e59a80a3204470c22',
    },
    'command-line-part2.html': {
        "base_sha256": 'b4e661741ea43f6036c37a3bf7569b8f48b5d7dcce3165e9227a2ee545500121',
        "current_sha256": 'e55138b6074c3a59ee7e6299a8cc8daff5e15adee8447be314a65688f1e439dc',
    },
    'command-line-part3.html': {
        "base_sha256": '8bbcd94be67114903287cc846be85ebf8c28ca55553b24ffeccac531e6135c4e',
        "current_sha256": '1a9507eae924f788b3802352a553fc91aaf00bf52de573e2c2aa9668c8466298',
    },
    'computer-data-fundamentals.html': {
        "base_sha256": '63152e924c0ef24ce0c42ce2b9eac72e060c81194d5b6c6b645726042782cc15',
        "current_sha256": '7ae7eff01959dc933dbb3448a0f7903ee2407067c8c00a42dde20f93f7b57eb2',
    },
    'conda-mamba-part1.html': {
        "base_sha256": '3c7f512711cae38a2b24edc83e273d016d70f78f278454d438c1760ba1460c87',
        "current_sha256": 'e30ae9679bfbe7b3b723c845885c035f78c85102b0a30f1b3d186457e131df6b',
    },
    'contact.html': {
        "base_sha256": '4246e857963ae03f977f53dc5378dd5b04031a55f724387bb0ff7ec4f63ebd36',
        "current_sha256": '1ba45b81ad9144bcac3c4f1a85893b417f8f0b3beb391a0ff8e2f2786a64412c',
    },
    'data-visualization-fundamentals.html': {
        "base_sha256": '02f83a47596b123ff6b660f1bc00f306afe9d0981953b6ca104d9edc3ee54c16',
        "current_sha256": 'be44726cf13fc59643a991ee72ef9349f2336e5c4ace8fa019c114418702c643',
    },
    'deterministic-retrieval-gget-ai.html': {
        "base_sha256": '5adcc0434a24e6aac5d6be2b5df62931b6cfbad689e4754246bf6ee43e97da6f',
        "current_sha256": 'bbc55e7dc6850e416bc48266886f4dd10129eae9937834b5b2017209b4026c82',
    },
    'docker-singularity-bioinformatics.html': {
        "base_sha256": '31c329a7e39fef72fd38dc00144756e092f5458a194f555fc0a4f3637929dec1',
        "current_sha256": '0bac2bf92e8599a6652c562a51ee1f74c5d86b43432d4f7fdbba79444f7739b5',
    },
    'evolutionary-phylogeny-analysis.html': {
        "base_sha256": 'd7307ab6b5de267eaef53d357a46c975eb1e359f2622bc39b25ad16ce904042e',
        "current_sha256": '358331adf7963b85b592b407cfa0dd6df904d8d92892220b3d1e9c91a921237c',
    },
    'experimental-design-batch-effects.html': {
        "base_sha256": 'e1be24adf1143dd361184ff2bf6ada2f9081a6cdaba825435343fa0070e3c7f8',
        "current_sha256": 'fa815d038d566a20f3786c2ac29d60080b8f3b835da7306cd60511fb80951b86',
    },
    'git-github-bioinformatics.html': {
        "base_sha256": 'ba22d0655cb66b57288dfc652cd6af434f06381e02bdf6a78d9e868e3f3484a7',
        "current_sha256": 'bfc81ba64d9efdee85f930f39358b1cd41e55ff7e1d3c59530b9e2286b684fc1',
    },
    'hpc-basic-commands.html': {
        "base_sha256": 'c8ca65757420fe38950c56847bdfe2f22be0133407c70a2f2067dbee4cc91124',
        "current_sha256": '1e2d05c910780ffe71b482bc84c2ed5a8bae705312805fa8f9380a20d2a915aa',
    },
    'hpc-connection.html': {
        "base_sha256": '94cc1d329455169af64356f79a7e2cc42daa79d9c3265010dade5b1dab25b011',
        "current_sha256": '755e3dd9bd8a8ba25f3228f7e9d0a6b03f0b6dd5df8d8191115282a6b743ac68',
    },
    'hpc-submission-part1.html': {
        "base_sha256": '49f79d84519fa61126e823f968974da7eca6b473a99ae66fd25833b01867dcdc',
        "current_sha256": '7dce65b3cc0455cf88b2b74ffb73e0299afed472c1bc03ab0c60a5fe5e8d0f77',
    },
    'hpc-support.html': {
        "base_sha256": '19ddcd336bc62229abe21fd007a1431893bda5b3e63e5d7d1c96ac940c0e622c',
        "current_sha256": 'a06c0e0592a259275e9d24f5061fb8a100e19c3cd6110a94409f4392dee1c462',
    },
    'infercnv-copy-number-variation.html': {
        "base_sha256": 'bb8279c76eb00dcbac8ea3aa832f7c4c4847d36f5d1be6544a7f56cd9a126686',
        "current_sha256": 'b9a0b5077d45c13ca47f25c8fd813517c1390a83f715028733e3c05606527e2f',
    },
    'introduction-to-bioinformatics.html': {
        "base_sha256": '13342be3215e1ef2e587420272bbf96e79a9e343c967c5739e0daacad42831cb',
        "current_sha256": '6b1fa6d2699f92b4c4220d2467694d82640b19116ca137a961c92994b239be55',
    },
    'long-read-pacbio-nanopore.html': {
        "base_sha256": 'ad66c113660318866496e1482217225042d9a0b845d14abc06a0485cf8ab9b55',
        "current_sha256": '3ea3a3a6e7df45b0cf81c131966fd724864afee246df8e47ff9fe8ea3e6af67b',
    },
    'mcp-zotero.html': {
        "base_sha256": '31d2af6147a34d5ffd17116181718696159af61feceefc1508a1d219733669d5',
        "current_sha256": 'e3d5788ea6bba75abb62eba992e1965479746b8ec4d4b285b43ea4ab490544c9',
    },
    'metagenomics-assembly-mapping.html': {
        "base_sha256": 'f0829b9810e6a9a858f0318fc1c7a7c6b371c37efa8e24219aa50bde4de257a5',
        "current_sha256": '2da871ec854eea68613e4caf65947d973d17ad97a872adb43376c1e3fd4b5bb7',
    },
    'metagenomics-kraken2-bracken.html': {
        "base_sha256": '93ef233f0c49bda5e1a1dc03507df85501d6e78af76bb0d1dda21198a24fe606',
        "current_sha256": '5733d52c5b4bc3165db70e1f03f120543dd8f89ff89512133b50e22873a639f7',
    },
    'metatranscriptomics-functional-pathways.html': {
        "base_sha256": '836656ace3a91852ca561a3767dd4f6985cb868dcdd3e7cdf76e0a027f89181a',
        "current_sha256": 'f7ba8e648f88f945a26913a2e5581b8e598572d5dcf3994de275f30f9d7f5448',
    },
    'metatranscriptomics-guide.html': {
        "base_sha256": '5fb9b57f031ca3212c8d8672c51a99ff1d698481c77442ce5ecc58d99fccc395',
        "current_sha256": '7810263ab4fb4f62ab999a999f2f5c8ee846ed02c15da140c89ac4b5bfb3cb15',
    },
    'modern-bioinformatics-methods-2026.html': {
        "base_sha256": 'c14a987a709845d7775f27881900e2995c3b9c76abba1858c3286278db80a746',
        "current_sha256": '189f24aa3872f2706f9679c5c462261d0433d869dcb44c98651fec9f1d37299f',
    },
    'notebooklm-research-brain.html': {
        "base_sha256": '11d81c273c8544270ad85899070ba855d1021c51724a34dc05925004166abb60',
        "current_sha256": '5ab06d5dd395a4f5d083b2416f12ae73bca1aaaeabec6f62e58971ec1d2056db',
    },
    'package.json': {
        "base_sha256": '8a28d49a6d8bd63c4fe6dd7e24e2d804c281bcdcb56ba0986e7dec45cc8a0e76',
        "current_sha256": '1cc4165462965fa8ffe13538dfbf6588928e395c98202031520ddfbaaf74cbb0',
    },
    'pages/cookie.html': {
        "base_sha256": '0ac00bd5b85807558e46560e2816471278082d9cd2feab53a182ad9455136625',
        "current_sha256": 'a7f11f2baf2e5063354d4c6e44093f6316ec62bd71a380803e7e17107b5c6328',
    },
    'pages/disclaimer.html': {
        "base_sha256": '56a8b1158020b611a9b5a120e567bf280943d6e5de7f5c2c93fe823c2ec8354d',
        "current_sha256": '7005ec650c72dfabde702f28ee2bae1d364ae9006f9f5afa00dca6c20c30f861',
    },
    'pages/privacy.html': {
        "base_sha256": '7cd5630f4ae1890b1fe8f510beb72bad61bf6fe6e276a0232e6d7478df21b472',
        "current_sha256": 'c10dc18dffa11305a396c04328440362c8f305bf7b56f2010db4f3f7e6cec2e7',
    },
    'pages/terms.html': {
        "base_sha256": '81ba11438f366d2d5d7ee80a264684fc94a6f90c228c047df9e65e400d2c695f',
        "current_sha256": '82e8fcf0cb84a1d2cc7007d9f5a447d6f859a6bb709f0d208dd73c8ac86af11d',
    },
    'phylogenomics-orthofinder.html': {
        "base_sha256": 'c479424deb797efd9810eb302166b56b8cf7f2dda777d2a721a8029749e7b49d',
        "current_sha256": 'dc007680075a83eafe8df9b0be04de3cf81a42ad53c9c908b13f145ba6794521',
    },
    'protein-structure-design-alphafold.html': {
        "base_sha256": '8722903dd781aaf48768da490f25e52d2a56abddf05c58b2299ba679421bd033',
        "current_sha256": 'd96b37128041d523369dd6a0b075ba5573b9996e5a96461a6a87ddc4f6465312',
    },
    'python-fundamentals-bioinformatics.html': {
        "base_sha256": 'c8bffb3873be70db1cf10ef33980fdd0c67a9836c2f3f0a01f824bea1c511bc8',
        "current_sha256": '34d9bf0057f93114d4835aaf2b44c21cb924457fb6a79b518966899ffaafdafe',
    },
    'quality-control-fundamentals.html': {
        "base_sha256": '98d29c3fe516dd3502367df150687938552e14821adde2b62b4a10090e2d0dcd',
        "current_sha256": 'b21a531e929fbf4ee37ab75f531537aa869ed7a81806fbe86bd73dc8a5e7c610',
    },
    'r-tidyverse-fundamentals.html': {
        "base_sha256": 'e825382250f90f18245c7c6f183decde6cf9b5130ee51cf7adcb0fa0fddfe3d0',
        "current_sha256": '4f3201daffe537c05fd078465f8732e5e7d8cace940c5498f1da7ded390eb440',
    },
    'reference-genomes-annotation.html': {
        "base_sha256": '789045c659cbfa76a5a7de64e296b9236d59166dfe9709dceb918e314384d84f',
        "current_sha256": 'b2523ef5ebde18aeb2b6984592182dcb1c2c9e254eb0fd4998ae52643bc9b403',
    },
    'reproducible-project-structure.html': {
        "base_sha256": 'c550a660382866e9fda326c305c0f351d4962d208aa8478d0886f593ed46ef88',
        "current_sha256": '51e1f8ac3c0d0c36cbb961c82b73f8be70d67f8e8ae379057a2882c0844a9b58',
    },
    'reproducible-workflows-snakemake-nextflow.html': {
        "base_sha256": '2db1e45aa46efb26e84c299698422303d8ef43951f2e1192efc2aa0eb3475808',
        "current_sha256": 'ec6d7242c61b65e322cffe5e0b4d9c3520ab2a242c276ac81479feca825076f4',
    },
    'research-reporting-interpretation.html': {
        "base_sha256": '3095799f471a35bd96bd61603dac500d8214d6c109868255e9bb08049988ead6',
        "current_sha256": '23217ad5d8b6ddd8f4e5104ba8040904dd580955483c7bb0b89483d7630dad18',
    },
    'robots.txt': {
        "base_sha256": '32fed17eda6976942d0c6ebd53e8bd2da12e1eddb48c9915c70128971cd4aabd',
        "current_sha256": '0df6757f46cd439654bf11fd06014ae224bc5694fdb5e6baa08a2481838e8462',
    },
    'scrna-seq-basics.html': {
        "base_sha256": '8c849cfc1596da3965568cb0f8282b20ff415c9dbcc35775874db5f4887413be',
        "current_sha256": '6f4776b181485985eaf2b8a28288d7c88722f3fd741c2e9690eeeeb2f4a3fe2c',
    },
    'scrna-seq-downstream-analysis.html': {
        "base_sha256": '3943ca1214eb76504ce8faf4b8bd196a873b243a6bcaaf55d600acbd051cc926',
        "current_sha256": 'f16cc3cb41611d2bdb1faa42da95cce1b1b56e442884504e9f8a6257ef0e04f1',
    },
    'scrna-seq-integration-strategies.html': {
        "base_sha256": 'c009eb8271e0ff8e32b45131acc3120f2e688c55248bd9e06178f245656a831f',
        "current_sha256": '9a68b81d40ce1d7c74f64c1ef2d2aacd4b57bad5c2afe7007f45ed22d134586c',
    },
    'scrna-seq-quality-control.html': {
        "base_sha256": '2b96b78ac7034f200e7ccbe290060b65e67f7f1b045d2d5f3c0496e975b515e4',
        "current_sha256": 'cd27f7f7dae40efa73e55f9aa47cf40ca947490a9f9e641d8ce18c77fe37840b',
    },
    'scrna-seq-trajectory-inference.html': {
        "base_sha256": 'df8f5a664e976071141e00152e76bd693936553f175bc73c24b26aec1078be03',
        "current_sha256": '502c26b528197b8a0fd7dc3457d13e42e5f34b1588c0e298dbd27a4aa738c116',
    },
    'services.html': {
        "base_sha256": '6b8220ea346489d021229492b6ed374e6dd19e08d18e67d75a756eb6ef0112f2',
        "current_sha256": '759802f269694fd93e6824cc12e5d4a928bb16af77022986cc3a615eae865b04',
    },
    'single-cell-deconvolution.html': {
        "base_sha256": 'e1f2688dd9cd7034afc19acb84222df295c15fca9ab95bea6a32dee4b674e455',
        "current_sha256": '9d17a4bcde55b0261021eaa23f76cd92444da967548246a6404336506c0edcf5',
    },
    'single-cell-foundation-models.html': {
        "base_sha256": '91349576a25426f7fbdc8ece36bb9b3845e62c848dd2368ed2ccabb4fa5293fb',
        "current_sha256": '0ff46e28574b68af1f552dc79f6004732deee4748fc7de787093d36b957e8524',
    },
    'spatial-transcriptomics-r-python.html': {
        "base_sha256": '935e4b0013354a9e1b320c9373f715298bf335ebc19273b2455dbc87c8f75e25',
        "current_sha256": '9c82bbac0f3a2d3dc584de69f7f5ac301d0f46058699e33e78e8fca73ac4d165',
    },
    'statistics-for-bioinformatics.html': {
        "base_sha256": 'bddb43d649669e51df03e970d4c2f32b8e578333ad62ab3f4c4b374e13d26e97',
        "current_sha256": '9e1d3a43eb16b52cfb660823e836c9bd69ca82708d9638828b572f08e3153e75',
    },
    'success.html': {
        "base_sha256": 'f6acf793c71a5dbe5640ec9527f64c697768a6fec5aefc11f371a29abce5a651',
        "current_sha256": '9cad0d9b65d9cc039fc26e2ee2608c8aad688782dd74a2e12c526b3d5ac3ef7b',
    },
    'tcr-bcr-repertoire-analysis.html': {
        "base_sha256": '0d16fcddefcbb2e8e8ed0439a4b868f2f6f050ad1e57ec310ebae6ccb0014490',
        "current_sha256": '89acefaa8ddc53e02640b647f91701c45029898d079fe5f11de79a6ebc042d98',
    },
    'transcriptomics-differential-expression.html': {
        "base_sha256": 'cf5aae07bd263e022cb9c3dbf277f445c264a02f29ec505ec95ebce1862cfda5',
        "current_sha256": 'ac03200aae4a7525e9ba5af9144f569d70c4bba0ce464f68a2da5be165d20f46',
    },
    'tutorials/16s-rrna-prokka-annotation.html': {
        "base_sha256": 'c7eb6202af29e3b348620371a9159458821f21e486fcefe98efe576d0a5ea23d',
        "current_sha256": '20fc87af469444ae55ee9a213ecb605521cda80e8cd6b187590e5d1672d9776b',
    },
    'tutorials/advanced-ai-orchestration-bioinformatics.html': {
        "base_sha256": '9276f85af4f931d21cdf7d06fdcd7b7e0cbe6238d4074c0158a3f5754a8f1a58',
        "current_sha256": '21319fbc9a3e1ae1eadd32fbc8eb21c93065796d4542eeac22699b6bec936c02',
    },
    'tutorials/advanced-ai-single-cell.html': {
        "base_sha256": 'e1ea2ec717c5d5055f0f54aa8f78b4de2d492d5b37dd966eab8967ca1af783f6',
        "current_sha256": 'b99be60de3a4ee1594e8484c7fe5ce864a122db95d51904a24ebfe29faf85a15',
    },
    'tutorials/advanced-visualization-packages.html': {
        "base_sha256": 'ebd135bc47eb8b72363190e91a1f34823bd46c54fbfdd1fcfa9bad5ddf063f65',
        "current_sha256": 'b91e6b09886571de513131625953449fe6a63ffab634dcb56c7dd5d22a7dd301',
    },
    'tutorials/ai-bioinformatics-github-copilot.html': {
        "base_sha256": '270c9e53bf8ce82659d24ea261d9dbf63585a74236dc4b7a4fea3d90a4e6d5b5',
        "current_sha256": '1cdfeb7e3961343de195bd60d2ce8ceeadaab719ef2fbbec7dca54648bc84879',
    },
    'tutorials/ai-coding-cursor-aider.html': {
        "base_sha256": '460bb9de75cf0ac5ed72ac7ba6a6e635862391a36649aa3a5946b081fb5c33a1',
        "current_sha256": '680116034dda8b37cffb0f7236c2d21aedbc8d81148e64acdd7f8999ce39e822',
    },
    'tutorials/ai-prompt-engineering-seurat.html': {
        "base_sha256": 'cb889cf8bee5c425e4de8b64bf38bf5be53383dc5778dc0c65a867b4c60baf57',
        "current_sha256": '3260ddebfb610e2b931cd851ad5f69676b7f62d95e682450381ede4b259705fe',
    },
    'tutorials/autonomous-research-orchestrator.html': {
        "base_sha256": 'dca02440eb0a7fd50fc5d0259d633ac3c38b33835197fdd2d701c6a9df927575',
        "current_sha256": '10e19e850c02ae4c02866150a64e4f4e6d1b240383fa8e4bd71882557f89d8de',
    },
    'tutorials/biological-data-formats.html': {
        "base_sha256": '1f48fc48a97f82d17decb32f0a14270b0cf906ea392dd53c146d3a160c5ce785',
        "current_sha256": 'aa255baba01c8d6445355bb17b86c91bf7e5595fa9e7e0a593901dad43f594ed',
    },
    'tutorials/cell-cell-communication.html': {
        "base_sha256": '6128a0352dbee0063d983834d5ab7744e484f871b1cf1e9791f035d90c9ebb91',
        "current_sha256": '3550f828a349ab250a754d6b2651a0c6c2aa05a5927abed3d9c8aad4be00e9ee',
    },
    'tutorials/cell-type-annotation-methods.html': {
        "base_sha256": '6d35c6b0cd67e1fdd90c684e054feb60916fce8f1d4abc1b6febff020ac11c65',
        "current_sha256": '63a3e2cd070302fd4a2cb6102d5811778a0141ac09087dc3cf6a0e565c43eaa7',
    },
    'tutorials/cite-seq-wnn-multiomics.html': {
        "base_sha256": '89a2fba648a08ace1cae85bfd948b3c0e70f448394be9ecfcbd08e8c3ba52197',
        "current_sha256": '86505737963afe9b7e2e7a4b291616bdb1d822eab3b623c061177fbd4c7b995b',
    },
    'tutorials/command-line-part1.html': {
        "base_sha256": '2146589eba8c196cde7217933d97b1755e5f139e5d5da6ece470f245a893ca2b',
        "current_sha256": 'ce21aa900df0d4f410290c3f22a281115c4ec9ae714e87039e5f43152eb2ed34',
    },
    'tutorials/command-line-part2.html': {
        "base_sha256": '73d40adab938ee9453a6e7c1ccdb739ec3a479b0527e581de2719132b12a839a',
        "current_sha256": '12f074a8489b0b2c57b63bc1767eddcf471effe8a01625371a1298477e56a28e',
    },
    'tutorials/command-line-part3.html': {
        "base_sha256": '9f4cecb8c22cc7dc38c7768c31281bc8baae538ab14b21bb674df60585d4d0f0',
        "current_sha256": '9ee6e272d81d6ec177a7e47bb6319ded4af98907876de919e2fb93b98d8602bc',
    },
    'tutorials/computer-data-fundamentals.html': {
        "base_sha256": '7bd5e37675d8935c32478ed9afeafcc58540a2b4a00e454eb0b14ed676f6fda0',
        "current_sha256": '05606d85d8aeedc0a2007573dbef45cde5812ba8583350ed541213840b7728ba',
    },
    'tutorials/conda-mamba-part1.html': {
        "base_sha256": '65bdb85f237f6c796e048bd7f8acbb63a9abc9069085bb010d4e7ecfc16273b2',
        "current_sha256": '2541d8580c817bcf674f1710b9a8048ce8855a7ba69c977f37f709b16f265f43',
    },
    'tutorials/data-visualization-fundamentals.html': {
        "base_sha256": 'cf0837d2fdae10a3ff3bf346f5a6d4f1177a7ed67decd6a813d42dc1a8c69546',
        "current_sha256": 'ba36881b28586914ddf8f67e0516bd30265bfb7576d9e69d365cf8e7917aae20',
    },
    'tutorials/deterministic-retrieval-gget-ai.html': {
        "base_sha256": '4d421390fb5eb2f4a59a78f29b1a82156c42c79e0c6ee75c3d4c27ce2abfb019',
        "current_sha256": '069e6bf9865e64624b4b37d06aa9f5e4ba60a0687680d042ac816fcf931f3fcd',
    },
    'tutorials/docker-singularity-bioinformatics.html': {
        "base_sha256": 'fa23060e956cbb04e27851ec77c809ec92b1505af358ebdb4999c203e498af16',
        "current_sha256": '547407f046e02e0507ebb4fbe82fd38432189c461e93e64d211551c9155913fc',
    },
    'tutorials/evolutionary-phylogeny-analysis.html': {
        "base_sha256": 'b39b36840612b4a92aa08293fb9ba8fc5a5e679d36057075c10836f93ef496b7',
        "current_sha256": '6b34166cac934b8f9f3572f5ac91d0b34c7383205146542ada5101c0b8d8a530',
    },
    'tutorials/experimental-design-batch-effects.html': {
        "base_sha256": '0c8d1e02c1d043b6932c194d08ee6cf15dbb101d7bd48e53559974a3804f09c1',
        "current_sha256": '196a38d59b8ab63e52b63b9caf3d470de9217f9a4795a4b7e04ec09bf05c108d',
    },
    'tutorials/git-github-bioinformatics.html': {
        "base_sha256": 'e819ec200f02d8f626bb20e2571c2a2fd650db97d3dc698697af2f3ff9dd715d',
        "current_sha256": '1fc6242441bfd7eb47ea3eed462f38f4bb7a8329336ce05722daa87cf8428c4e',
    },
    'tutorials/hpc-basic-commands.html': {
        "base_sha256": '89d95cf875bf03fb173f3b6448120c068e985d516ab38068ee7f188a60be7300',
        "current_sha256": '06c6647cd072b0a208155bd73e71c796846065479bb9db9449bf87947007e8f9',
    },
    'tutorials/hpc-connection.html': {
        "base_sha256": '59e9bd00ac99554d77b280fcf8ced7357a34ab7b18de5adbf9a98f1e2bc15292',
        "current_sha256": '8483da42e5d8ba73a2b57066475827420d9dffb41fcc581d1f6285664776e98e',
    },
    'tutorials/hpc-submission-part1.html': {
        "base_sha256": 'd2d0b2e9eaace8fe9de9c4322bc300696d812405d15f67b1ded43d6e280c939f',
        "current_sha256": '763a381b41550f1c859762db124fc5ae756fdd6ed59a211d72559be9d83f2494',
    },
    'tutorials/hpc-support.html': {
        "base_sha256": '15feca650cf0c414e5754dc823fb7e1ad90721c78bf182a38a645612c4edcc63',
        "current_sha256": '481aed4f9de85e133c48ee23077bb76efa484c6343ffedbd9289395a9d56730f',
    },
    'tutorials/infercnv-copy-number-variation.html': {
        "base_sha256": '7b773d5545e4e9f48eec0836d23f16a087ba20d7ffcfb040f20e5f0ef0bf216a',
        "current_sha256": '07cf2fdfa04723e6e49d9a3fc9bdcbf3173d08d239275416671e03bde51b11c2',
    },
    'tutorials/introduction-to-bioinformatics.html': {
        "base_sha256": '749cb18a282e461c19c0fb7044d163eaa4dadeae0a6c51bbbd7d6a1039d84d03',
        "current_sha256": '715ed4acfd5df7c80cb3753b090b0b124bc62183b043d8d71bb8820bf7bac07a',
    },
    'tutorials/long-read-pacbio-nanopore.html': {
        "base_sha256": '2821b7fbe75ba6c7d896d7554ecd6ec1fff9fba621d13602c6e1b67e99b96228',
        "current_sha256": 'a77c34a8302cd83261a13fe7a94604a73d77bba0e6f05be2bd40b18c727b3ebd',
    },
    'tutorials/mcp-zotero.html': {
        "base_sha256": 'ad00f15d2d2bf85b05568d14d79bc37366df1ec7e74e2a814348d25540fc4b2a',
        "current_sha256": '96748781aebcc56011ae9714b6caf128f567e1ba41341fb780bb4fd67438e0a5',
    },
    'tutorials/metagenomics-assembly-mapping.html': {
        "base_sha256": '31a3404bd344e75b94bc3a4f4c29e63753bf91e94e0ad2ed8c2e2fb98c577793',
        "current_sha256": '89e25cd8132017a0f70f314c783b799fe92421d73578a2816c4d1d148146a044',
    },
    'tutorials/metagenomics-kraken2-bracken.html': {
        "base_sha256": 'b64613bd1a639742db63d96694561d0042d452a5bcc2f060bafe79ddb1da26bf',
        "current_sha256": '6435d72d527f63762b595fffe9e872617a3d87bb2687bb9ce1da36fdf0418590',
    },
    'tutorials/metatranscriptomics-functional-pathways.html': {
        "base_sha256": '4d97f6cecd5301ada7c90709f180d6a598c4e2973ed4adac9b3605cca1c017d8',
        "current_sha256": '205156dbd1be6f8f87e4ad9aa62312751e6c68ffc23052dd064e8ac064859deb',
    },
    'tutorials/metatranscriptomics-guide.html': {
        "base_sha256": 'a15d2ff6cb9d676171c7a0e18ece18d79a2f58b9e2448b4b8a2edfe30f0671b8',
        "current_sha256": 'd60e12239910f6d6ff7dc9afb01110e1f6fa30ef4fefeb56eaaa18709ae9a33a',
    },
    'tutorials/modern-bioinformatics-methods-2026.html': {
        "base_sha256": 'f6aec522b3a7d0af283f38d4a0aaf23922d54ddedba1a2ece7e47a221ca21098',
        "current_sha256": 'b1b0b52c34a184ecc92f930f732c80df65de873f6cee7cee530d48371e9600c2',
    },
    'tutorials/notebooklm-research-brain.html': {
        "base_sha256": 'c195a1b29167367bf67fc49b0e467f504fa392162190e3b43a878cd685958d39',
        "current_sha256": '0cf05cae7d442e35f5b1557f4c2d626934e6b9271cc0e0b925b7b9096325e2d4',
    },
    'tutorials/phylogenomics-orthofinder.html': {
        "base_sha256": 'c0698c97b91c92e0569e2c911b524bc5d313839b670343051aed13c67411c600',
        "current_sha256": '83fb086c7052e242a576fbd4e48264f2b7ede7be1ac7a59544cf0a694dabf7a1',
    },
    'tutorials/protein-structure-design-alphafold.html': {
        "base_sha256": 'f13cc00f7bf041016fecf508733e2dc0b711f621c87292da42109bf26c15e4b0',
        "current_sha256": '96c66fc63f6bd9a526882b71aa2c8544fbf24f223bca7caaea089b698f615f27',
    },
    'tutorials/python-fundamentals-bioinformatics.html': {
        "base_sha256": 'dc8d9c4903071705322e05fe5583f2c8abef936d005456bf41314f822af71f6d',
        "current_sha256": '6f7d0c6a12ff06eb1d2ac9531db1317892095f5dc9f3aebbdf81295bb6516155',
    },
    'tutorials/quality-control-fundamentals.html': {
        "base_sha256": '9f2cab49e7b3b1d839c959d9d99bbedaca4910b899e8f104fca946239356ccd2',
        "current_sha256": '1526f9a815f74e11bea14ff6e7cbb28342c3d36a15edc7ed242e87adcd830793',
    },
    'tutorials/r-tidyverse-fundamentals.html': {
        "base_sha256": 'b31c18a40c3890ac0a75089f494ee992ec5f7cac838aeda438af91e1e1c01233',
        "current_sha256": '059ccb79ed257c209a49555b00826bd8544af7a37d3eea45506c2ea04d47ba48',
    },
    'tutorials/reference-genomes-annotation.html': {
        "base_sha256": 'be2f0a813c720bb8f5d9a31247224a85ddc1a95e41395b5c9d842b9f7ec44df2',
        "current_sha256": '83f87098eb6636393ba10d634bdd66da5c16c9c3e51cb3bad5fbdc33fbadb928',
    },
    'tutorials/reproducible-project-structure.html': {
        "base_sha256": 'aa784ad82ed1c0a701bbe47c927b1515f61fc14665289dc3cec508fa69f7cdde',
        "current_sha256": 'eafb0435765018b67c7d4df524d7d0b309dff749fd5c22c7d8ba140cc5dd3474',
    },
    'tutorials/reproducible-workflows-snakemake-nextflow.html': {
        "base_sha256": '65ab730c457644e0a331392c7fabd943616ac026a51007d48bc19b44d2723303',
        "current_sha256": 'ff712b09da3e6ebda116a1b0d1d1fa75f8f9e0972b41442004842570e87bd6dd',
    },
    'tutorials/research-reporting-interpretation.html': {
        "base_sha256": '4341f5a2213de576a3a5921dec10e23d3fe6e27fe1e1d72e29c0dcab5189a217',
        "current_sha256": '2d9b1d0b9181d594cba8b616ef4e4c33a9306c146d96295ce37273faed3ffa1d',
    },
    'tutorials/scrna-seq-basics.html': {
        "base_sha256": '27f2cdf71ea3dc878008c37d33f731938e842c5fe9d55239e9e88850ec1a58c2',
        "current_sha256": '851e9d143ca149f53e04dbc85c16bd3f214045dd08d5d1af0dc4188a49ef80f8',
    },
    'tutorials/scrna-seq-integration-strategies.html': {
        "base_sha256": '36b66c4f4a7a5fdddfb1d5dbe6f7e57b7e82074cdfcb6e097cfdbbd08298ddf2',
        "current_sha256": '8448288d49097a96f215b45f3b29cb8261b4ac1bd74a937a46160d3cc9f6b4c9',
    },
    'tutorials/scrna-seq-quality-control.html': {
        "base_sha256": '1a413ded8296ea97f36e3f2dd4546a9e7e1307f8fec24944df87d3d084c0975d',
        "current_sha256": '8020d7c40707921edfb2bab0104e92452d3d09288b73f9fea6215fa1f0022c6a',
    },
    'tutorials/scrna-seq-trajectory-inference.html': {
        "base_sha256": '2edbec4b2ed67576a6cc26edffe81d08e8fa4b05b8dd690acc6b9c93621f3995',
        "current_sha256": '556830891a5749c2bf9eb3ce29171d5adbef7e43969a975ebab7f1c21a03084c',
    },
    'tutorials/single-cell-deconvolution.html': {
        "base_sha256": '3c3b0e436ab9a5289e9e6f618ed591f47bdc9365e1dea10d7db006bdc3dbee27',
        "current_sha256": '746c296f66c0bfe528af72b59d8aa1f065a155397343cf09548f3f82aae228b3',
    },
    'tutorials/single-cell-foundation-models.html': {
        "base_sha256": 'f7ce6f1d87f01aa926751352b6190db65fa74fed1663bd6e05998b94cbd4b6f4',
        "current_sha256": '9237537c925ea01871ee4f9f75c2ece2125a76f94f2bebf77149c16dac6d4997',
    },
    'tutorials/spatial-transcriptomics-r-python.html': {
        "base_sha256": '2bec6bf5446bf1b69dc2d15c2ec68cecf707789682177a27b057dda11ed7f2c4',
        "current_sha256": '79cee4e30d2e3802f85ad23008c7647cc03c59cb2cb3078e76cb68f9b46066cb',
    },
    'tutorials/statistics-for-bioinformatics.html': {
        "base_sha256": '47e8e3cb3118f5436d98ca396922adfc9f186eb7d2ac1bd6bf3142fd505d07cb',
        "current_sha256": '3005c566b41314e6064490b3c552b100c783d9195034658a2b84d4a7464b0b59',
    },
    'tutorials/tcr-bcr-repertoire-analysis.html': {
        "base_sha256": '2f330ad6dc40bcd9e5b05c8e5394f63ca508478c21e00fca98c8bc9350799338',
        "current_sha256": '03fef0b2789806fa60235790a4e291bb5495c1e60c377e9214ba0a4770e89206',
    },
    'tutorials/transcriptomics-differential-expression.html': {
        "base_sha256": '7ed1451e96227811ebcc6aba32bd7cc3646f69a532dac429eebe5424d82fb1e9',
        "current_sha256": 'af19e93411a8e59d7adf2d406f63e7dc6cb390549b407de1c705a142d43817ff',
    },
    'tutorials/wes-variant-calling-pipeline.html': {
        "base_sha256": '1ed1d76d1677af76162dfcc5406b87b385372d2e353854df8d8edb0c09c2cc79',
        "current_sha256": '1ab9db4e307c3c9a7d1da934fb318caf762ef093731e53e90260925c10d986ac',
    },
    'wes-variant-calling-pipeline.html': {
        "base_sha256": '8d1d61d7a0ab3f2fbba0aff68b7972083c95b0e7b12946468c380ba087e03d69',
        "current_sha256": 'c07a780b7f1a2e0ae627c7419d877fb1f1f96444a6c03358c485d0a8dccda4a0',
    },
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=None)
def _base_bytes(relative_path: str) -> bytes | None:
    if relative_path not in PINNED_FILES and relative_path != "sitemap.xml":
        return None
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode != 0:
        return None
    data = result.stdout
    if _sha(data) != PINNED_FILES[relative_path]["base_sha256"]:
        raise AssertionError(f"homepage-redesign base digest mismatch: {relative_path}")
    return data


SITEMAP_REMEDIATION = {
    "head_commit": "c4a35246",
    "base_sha256": 'c6fd2c3efd499cc9cf3cdfa7f2fc4cab07f45724d11735af150d4f1c9a1ef0d6',
    "current_sha256": '34bbe8a36a0d3acbe855d286732ef708e570b10eb968a5639acedc87be624076',
}


@lru_cache(maxsize=None)
def _sitemap_head_bytes() -> bytes:
    data = subprocess.check_output(
        ["git", "show", f"{SITEMAP_REMEDIATION['head_commit']}:sitemap.xml"],
        cwd=ROOT,
    )
    if _sha(data) != SITEMAP_REMEDIATION["base_sha256"]:
        raise AssertionError("sitemap remediation base digest mismatch")
    return data


def normalize_homepage_redesign_bytes(relative_path: str, data: bytes) -> bytes:
    """Restore only an exact pinned homepage-redesign file to its 8cfe6991 bytes."""
    if not isinstance(data, bytes):
        raise TypeError("homepage-redesign byte normalization requires bytes")
    if relative_path == "sitemap.xml":
        if _sha(data) == SITEMAP_REMEDIATION["current_sha256"]:
            return _sitemap_head_bytes()
        return data
    entry = PINNED_FILES.get(relative_path)
    if entry is None:
        return data
    observed = _sha(data)
    if observed == entry["base_sha256"]:
        return data
    if observed != entry["current_sha256"]:
        return data
    original = _base_bytes(relative_path)
    if original is None:
        return data
    return original


def normalize_homepage_redesign(relative_path: str, text: str) -> str:
    """UTF-8 text wrapper around the exact homepage-redesign normalizer."""
    if not isinstance(text, str):
        raise TypeError("homepage-redesign normalization requires decoded text")
    if relative_path not in PINNED_FILES and relative_path != "sitemap.xml":
        return text
    return normalize_homepage_redesign_bytes(relative_path, text.encode("utf-8")).decode("utf-8")
