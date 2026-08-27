import json
import re
import urllib.parse
from collections import defaultdict
from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "_content-extract"
ASSETS = ROOT / "assets"
TEAM_ASSETS = ASSETS / "team"
PORT_ASSETS = ASSETS / "portfolio"

for d in [TEAM_ASSETS, PORT_ASSETS, ROOT / "team", ROOT / "projects", ROOT / "portfolio", ROOT / "publications", ROOT / "news"]:
    d.mkdir(parents=True, exist_ok=True)

NAV = [
    ("Home", "index.html"),
    ("Team", "team/index.html"),
    ("Projects", "projects/index.html"),
    ("Publications", "publications/index.html"),
    ("Portfolio", "portfolio/index.html"),
    ("Teaching", "teaching.html"),
    ("News", "news/index.html"),
    ("Awards", "awards.html"),
    ("Contact", "contact.html"),
]


def rel(from_path: Path, to_href: str) -> str:
    """Relative URL from a page file to a site-root-relative href."""
    depth = len(from_path.relative_to(ROOT).parts) - 1
    prefix = "../" * depth if depth > 0 else ""
    return prefix + to_href


def nav_html(page: Path, current: str) -> str:
    items = []
    for label, href in NAV:
        url = rel(page, href)
        cur = ' aria-current="page"' if current == href else ""
        items.append(f'<li><a href="{url}"{cur}>{escape(label)}</a></li>')
    logo = rel(page, "index.html")
    css = rel(page, "css/site.css")
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css}" />
</head>
<body>
  <header class="site-header">
    <div class="wrap nav-inner">
      <a class="logo" href="{logo}">Control of HVDC/AC Power Systems<span>TU Delft · IEPG</span></a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
      <ul class="site-nav" id="site-nav">
        {"".join(items)}
      </ul>
    </div>
  </header>
'''


FOOTER_LINKS = """
"""


def footer_html(page: Path) -> str:
    js = rel(page, "js/site.js")
    return f'''
  <footer class="site-footer">
    <div class="wrap footer-grid">
      <div>
        <div class="brand-font">Control of HVDC/AC Power Systems</div>
        Intelligent Electrical Power Grids · Electrical Sustainable Energy · TU Delft
      </div>
      <div>
        <h3>Explore</h3>
        <ul>
          <li><a href="{rel(page, "team/index.html")}">Team</a></li>
          <li><a href="{rel(page, "projects/index.html")}">Projects</a></li>
          <li><a href="{rel(page, "publications/index.html")}">Publications</a></li>
          <li><a href="{rel(page, "teaching.html")}">Teaching</a></li>
          <li><a href="{rel(page, "portfolio/index.html")}">Open-source portfolio</a></li>
        </ul>
      </div>
      <div>
        <h3>Contact</h3>
        <ul>
          <li><a href="mailto:A.Lekic@tudelft.nl">A.Lekic@tudelft.nl</a></li>
          <li>+31 15 27 82461</li>
          <li>Room 36.LB 03.210</li>
          <li><a href="https://github.com/control-protection-grids-tudelft" target="_blank" rel="noopener">GitHub org</a></li>
        </ul>
      </div>
    </div>
  </footer>
  <script src="{js}"></script>
</body>
</html>
'''


def write(page: Path, title: str, current: str, body: str):
    html = nav_html(page, current).replace("__TITLE__", escape(title) + " · HVDC/AC Control · TU Delft") + body + footer_html(page)
    page.write_text(html, encoding="utf-8")
    print("wrote", page.relative_to(ROOT))


def make_avatar(slug: str, initials: str, colors=("0b3a45", "1f9a88")):
    """Create initials placeholder only when no real portrait exists."""
    path = TEAM_ASSETS / f"{slug}.jpg"
    if path.exists() and path.stat().st_size > 5000:
        return path
    img = Image.new("RGB", (640, 640), "#" + colors[0])
    draw = ImageDraw.Draw(img)
    # soft circle
    draw.ellipse((40, 40, 600, 600), fill="#" + colors[1])
    draw.ellipse((90, 90, 550, 550), fill="#" + colors[0])
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 160)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((640 - tw) / 2, (640 - th) / 2 - 10), initials, fill="#c8ebe3", font=font)
    img.save(path, quality=90)
    return path


def make_portfolio_image(slug: str, label: str, tone=0):
    """Keep curated Interoperability Program visuals; placeholder only if missing."""
    path = PORT_ASSETS / f"{slug}.jpg"
    if path.exists() and path.stat().st_size > 20000:
        return path
    tones = [
        ((6, 24, 32), (31, 154, 136)),
        ((11, 58, 69), (46, 196, 174)),
        ((8, 32, 40), (140, 110, 60)),
        ((20, 40, 48), (80, 160, 150)),
    ]
    c1, c2 = tones[tone % len(tones)]
    img = Image.new("RGB", (1200, 750), c1)
    draw = ImageDraw.Draw(img)
    for i in range(8):
        y = 80 + i * 80
        draw.line((0, y, 1200, y + (i - 4) * 12), fill=c2, width=2)
    draw.rectangle((0, 620, 1200, 750), fill=(6, 24, 32))
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 42)
    except Exception:
        font = ImageFont.load_default()
    draw.text((48, 650), label, fill=(200, 235, 227), font=font)
    img.save(path, quality=88)
    return path


# ---------- Data ----------
TEAM = [
    {
        "slug": "aleksandra-lekic",
        "name": "Dr. Dipl.-Ing. Aleksandra Lekić",
        "role": "Associate Professor · Group lead",
        "project": "All programmes",
        "email": "A.Lekic@tudelft.nl",
        "type": "pi",
        "status": "current",
        "years": "2020–present",
        "bio": "Aleksandra received B.S., M.S., and Ph.D. degrees in electrical engineering from the University of Belgrade (2012, 2013, 2017). After roles at the University of Belgrade and a postdoc at KU Leuven / EnergyVille, she joined TU Delft in 2020 (Assistant Professor) and became Associate Professor in May 2025. She leads the Control of HVDC/AC Power Systems team on circuit theory, nonlinear control, harmonic stability, and real-time validation of hybrid AC/DC and HVDC systems. NWO Veni 2022 laureate. Associate Editor for IEEE Transactions on Power Delivery and the International Journal of Electrical Power & Energy Systems; Senior Member, IEEE; represents TU Delft in the CRESYM General Assembly.",
        "keywords": ["HVDC control", "Harmonic stability", "MPC", "Interoperability"],
        "links": [
            ("Staff page", "https://www.tudelft.nl/staff/a.lekic/"),
            ("Google Scholar", "https://scholar.google.com/citations?user=xwCWAb0AAAAJ&hl=en"),
            ("GitHub org", "https://github.com/control-protection-grids-tudelft"),
        ],
    },
    {
        "slug": "rohan-kamat-tarcar",
        "name": "Rohan Kamat Tarcar",
        "role": "PhD researcher",
        "project": "InterOPERA",
        "type": "phd",
        "status": "current",
        "years": "2023–2027",
        "bio": "PhD candidate at TU Delft on hybrid control strategies for MMC-based HVDC transmission networks (InterOPERA). His research develops stability-based switching between grid-following and grid-forming modes using polytopic Lyapunov functions, with real-time simulation and control-hardware-in-the-loop validation under weak-grid, SCR variation and AC/DC fault conditions. MSc Electrical Power Engineering, TU Delft (2023).",
        "keywords": ["Hybrid GFL/GFM", "MMC", "Lyapunov switching", "CHIL"],
        "links": [("Project", "projects/interopera.html")],
    },
    {
        "slug": "arjita-pal",
        "name": "Dr. Arjita Pal",
        "role": "Postdoctoral researcher",
        "project": "InterOPERA",
        "type": "postdoc",
        "status": "current",
        "years": "2025–ongoing",
        "bio": "Postdoctoral researcher on InterOPERA, contributing to multi-vendor multi-terminal HVDC interoperability — functional and technical integration frameworks, interaction studies and real-time physical demonstrator work for modular, interoperable control and protection with grid-forming capability.",
        "keywords": ["HVDC interoperability", "Multi-vendor grids", "GFM"],
        "links": [("Project", "projects/interopera.html")],
    },
    {
        "slug": "saif-alsarayreh",
        "name": "Saif Alsarayreh",
        "role": "PhD researcher",
        "project": "HARMONY",
        "type": "phd",
        "status": "current",
        "years": "2024–2028",
        "bio": "PhD researcher on HARMONY (CRESYM) developing a unified dynamic-phasor (DQsym) modelling framework for hybrid AC/MTDC systems — bridging RMS and EMT for harmonic state-space analysis and impedance-based stability assessment. B.Sc. Mutah University (2016); M.Sc. Budapest University of Technology and Economics (2019). Formerly Lead HV/LV Power System Engineer at Jaguar Land Rover.",
        "keywords": ["Dynamic phasors", "DQsym", "Harmonic stability", "MTDC"],
        "links": [("Project", "projects/harmony.html"), ("DQsym repo", "https://github.com/control-protection-grids-tudelft/DP")],
    },
    {
        "slug": "haixiao-li",
        "name": "Dr. Haixiao Li",
        "role": "Postdoctoral researcher",
        "project": "HARMONY",
        "type": "postdoc",
        "status": "current",
        "years": "2023–ongoing",
        "bio": "Postdoctoral researcher on HARMONY developing the unified Harmony software framework — symbolic/numerical modelling, AC/DC optimal power flow and impedance-based harmonic stability assessment for converter-dominated hybrid grids. Lead contributor to the open ACDC-OpFlow / OpFlowTools cross-language OPF stack.",
        "keywords": ["AC/DC OPF", "Harmony toolbox", "Symbolic modelling"],
        "links": [("Project", "projects/harmony.html"), ("ACDC-OpFlow", "https://github.com/CRESYM/ACDC_OPF")],
    },
    {
        "slug": "sunny-singh",
        "name": "Dr. Sunny Singh",
        "role": "Postdoctoral researcher",
        "project": "SAFE-GRID",
        "type": "postdoc",
        "status": "current",
        "years": "2024–2025",
        "bio": "Postdoctoral researcher on SAFE-GRID (NWO Veni), developing data-driven model predictive control that brings PE converter execution toward the microsecond range for stable multi-terminal, multi-vendor HVDC operation under large disturbances. B.Sc./M.Sc. Applied Mathematics (DDU Gorakhpur, 2014/2016); Ph.D. Mathematics, IIT (BHU) Varanasi (2024). Research interests: nonlinear dynamics, control theory, neural networks and system identification.",
        "keywords": ["MPC", "Data-driven control", "SAFE-GRID", "Neural networks"],
        "links": [("Project", "projects/safe-grid.html")],
    },
    {
        "slug": "tuanku-badzlin-hashfi",
        "name": "Tuanku Badzlin Hashfi",
        "role": "PhD researcher",
        "project": "Inter-oPEn",
        "type": "phd",
        "status": "current",
        "years": "2024–2028",
        "bio": "MSCA doctoral fellow on Inter-oPEn developing grid-forming control for offshore wind farms in MMC-HVDC networks, internal submodule fault-tolerant control (per-SM and clustered faults), and Power Hardware-in-the-Loop validation. B.Eng. (Hons.) National University of Malaysia (2015); M.Eng.Sc. University of Malaya (2021); research assistant at UAEU until 2024.",
        "keywords": ["GFM OWFs", "MMC faults", "PHIL", "MSCA"],
        "links": [("Project", "projects/inter-open.html"), ("Official site", "https://inter-open.eu/")],
    },
    {
        "slug": "victor-reyes-dreke",
        "name": "Dr. Victor Daniel Reyes Dreke",
        "role": "Postdoctoral researcher",
        "project": "PROSECCO",
        "type": "postdoc",
        "status": "current",
        "years": "2025–ongoing",
        "bio": "Postdoctoral researcher on PROSECCO focusing on DC protection near HVDC converters, fault-ride-through co-design, and HIL demonstration of protection and control units (PACS) in the RTDS laboratory toward TenneT DC-substation demonstration. Uses robust control, MPC and machine learning for vendor-agnostic, disturbance-resilient converter and network control. B.Sc. Automation (Havana, 2017); M.Sc. System Electronics (USP, 2020); Ph.D. Eindhoven University of Technology (2024).",
        "keywords": ["DC protection", "MPC", "HIL", "PROSECCO"],
        "links": [("Project", "projects/prosecco.html")],
    },
    {
        "slug": "rahul-rane",
        "name": "Rahul Rane",
        "role": "PhD researcher",
        "project": "PROSECCO",
        "type": "phd",
        "status": "current",
        "years": "2024–2028",
        "bio": "PhD researcher on PROSECCO developing advanced DC protection algorithms and control–protection coordination for multi-terminal HVDC and hybrid AC/DC systems, validated on controller hardware-in-the-loop platforms. B.Tech. VJTI Mumbai (2021); M.Sc. Electrical Power Engineering, TU Delft (2024). Interests: modelling, stability analysis, control and machine learning in PE-dominated grids.",
        "keywords": ["DC protection", "Control–protection coordination", "cHIL"],
        "links": [("Project", "projects/prosecco.html")],
    },
    {
        "slug": "hongjin-du",
        "name": "Hongjin Du",
        "role": "PhD researcher",
        "project": "CSC",
        "type": "phd",
        "status": "current",
        "years": "2022–2026",
        "bio": "PhD researcher (China Scholarship Council) on coordinated optimal control of hybrid AC–MTDC systems: OPF-integrated droop control unifying system-level optimisation with decentralised converter control, plus forecast-integrated and chance-constrained extensions for offshore-wind uncertainty, validated in HIL/RTDS. Formerly Project Manager and Electrical Engineer at CHDER (China Huadian).",
        "keywords": ["AC-MTDC OPF", "Droop coordination", "Wind uncertainty"],
        "links": [],
    },
    {
        "slug": "hao-xu",
        "name": "Dr. Hao Xu",
        "role": "Postdoctoral researcher",
        "project": "MITIGATE-HARM",
        "type": "postdoc",
        "status": "current",
        "years": "2025–ongoing",
        "bio": "Postdoctoral researcher on MITIGATE-HARM extending the open-source Harmony toolbox for accurate, efficient impedance-based identification of converter-driven instabilities and harmonic resonances, and for automated mitigation / wideband passivity measures — cross-validated with DPsim and applied to TenneT large-scale cases. B.S. and Ph.D. Zhejiang University (2019, 2024). Research interests: power-system stability analysis and control.",
        "keywords": ["Impedance-based stability", "Harmony", "Harmonic mitigation"],
        "links": [("Project", "projects/mitigate-harm.html"), ("Official site", "https://mitigate-harm.eu/")],
    },
    {
        "slug": "muhammad-noman-ashraf",
        "name": "Dr. Muhammad Noman Ashraf",
        "role": "Postdoctoral researcher",
        "project": "MITIGATE-HARM",
        "type": "postdoc",
        "status": "current",
        "years": "2026–ongoing",
        "bio": "Postdoctoral researcher on MITIGATE-HARM contributing to open tooling for converter-driven stability and harmonic assessment in hybrid AC/DC systems. M.S. Electrical Engineering, Soongsil University (2019); R&D engineer at OKY Ltd. (Seoul) on inverter-based dynamic voltage compensators; Ph.D. research at Khalifa University. Interests: industrial harmonics, PLLs, robust voltage/current control for DVCs, and grid-forming inverter control.",
        "keywords": ["Harmonics", "GFM inverters", "DVC control"],
        "links": [("Project", "projects/mitigate-harm.html"), ("Official site", "https://mitigate-harm.eu/")],
    },
    # ----- TU Delft collaborators (listed on official TUD project pages / group decks) -----
    {
        "slug": "robert-dimitrovski",
        "name": "Dr. Robert Dimitrovski",
        "role": "Postdoctoral researcher · TenneT / TU Delft",
        "project": "HARMONY · MITIGATE-HARM",
        "type": "postdoc",
        "status": "collaborator",
        "years": "HARMONY–ongoing",
        "bio": "Experienced research associate at TenneT TSO GmbH with a part-time postdoctoral affiliation at TU Delft. Listed on the TU Delft HARMONY page and in the MITIGATE-HARM TUD team; contributes to EMT/power-system modelling and Harmony / AC/DC OPF collaboration. Strong background in MATLAB, power transmission and EMT tools.",
        "keywords": ["EMT", "TenneT", "HARMONY", "AC/DC grids"],
        "links": [("Project", "projects/harmony.html"), ("MITIGATE-HARM", "projects/mitigate-harm.html")],
    },
    {
        "slug": "aditya-shekhar",
        "name": "Dr.ir. Aditya Shekhar",
        "role": "Assistant Professor · collaborator",
        "project": "SUNRISE",
        "type": "faculty",
        "status": "collaborator",
        "years": "SUNRISE 2023–2025",
        "bio": "Listed on the TU Delft SUNRISE project page as part of the TUD team with Aleksandra Lekić and Vaibhav Nougain. Research interests include power electronics systems and real-time / power hardware-in-the-loop validation.",
        "keywords": ["Power electronics", "HIL", "SUNRISE"],
        "links": [("Project", "projects/sunrise.html")],
    },
    {
        "slug": "pedro-vergara",
        "name": "Dr. Pedro P. Vergara Barrios",
        "role": "Assistant Professor · collaborator",
        "project": "BiGER Explore",
        "type": "faculty",
        "status": "collaborator",
        "years": "BiGER 2023–2024",
        "bio": "Listed as a responsible investigator on the TU Delft BiGER Explore page together with Aleksandra Lekić and Rashmi Prasad. IEPG collaborator on converter-dominated system modelling and open benchmarks bridging EMT and RMS approaches.",
        "keywords": ["Power systems", "Optimisation", "BiGER"],
        "links": [("Project", "projects/biger-explore.html")],
    },
    {
        "slug": "marjan-popov",
        "name": "Prof. Dr. Marjan Popov",
        "role": "Professor · collaborator",
        "project": "InterOPERA · protection research",
        "type": "faculty",
        "status": "collaborator",
        "years": "InterOPERA",
        "bio": "Professor at TU Delft (IEPG / Protection Centre). Appears on the group’s InterOPERA research-team materials with Aleksandra Lekić; long-standing collaborator on HVDC control, protection and multi-vendor interaction studies.",
        "keywords": ["HVDC protection", "InterOPERA", "Power system protection"],
        "links": [("Project", "projects/interopera.html")],
    },
    {
        "slug": "remko-koornneef",
        "name": "Remko Koornneef",
        "role": "Laboratory engineer · collaborator",
        "project": "PROSECCO · InterOPERA",
        "type": "staff",
        "status": "collaborator",
        "years": "Lab support",
        "bio": "TU Delft RTDS / laboratory engineer supporting hardware-in-the-loop demonstration work. Listed with the InterOPERA and PROSECCO project teams in group research presentations.",
        "keywords": ["RTDS", "HIL", "Laboratory"],
        "links": [("PROSECCO", "projects/prosecco.html"), ("InterOPERA", "projects/interopera.html")],
    },
    # ----- Legacy / alumni (from CV supervision list) -----
    {
        "slug": "farzad-dehghan-marvasti",
        "name": "Dr. Farzad Dehghan Marvasti",
        "role": "Postdoctoral researcher (alumni)",
        "project": "InterOPERA",
        "type": "postdoc",
        "status": "legacy",
        "years": "2022–2026",
        "bio": "Former postdoctoral researcher on InterOPERA, contributing to offline and real-time SIL/HIL interaction studies of multi-vendor HVDC demonstrators in PSCAD/EMTDC and RSCAD/RTDS.",
        "keywords": ["Multi-vendor HVDC", "SIL/HIL", "Interaction studies"],
        "links": [("Project", "projects/interopera.html")],
    },
    {
        "slug": "reza-bakhshi-jafarabadi",
        "name": "Dr. Reza Bakhshi-Jafarabadi",
        "role": "Postdoctoral researcher (alumni)",
        "project": "InterOPERA",
        "type": "postdoc",
        "status": "legacy",
        "years": "2022–2026",
        "bio": "Former postdoctoral researcher on InterOPERA, working with the TU Delft team on multi-vendor HVDC interaction studies and related control/protection research.",
        "keywords": ["HVDC", "Microgrids", "InterOPERA"],
        "links": [("Project", "projects/interopera.html")],
    },
    {
        "slug": "azadeh-kermansaravi",
        "name": "Dr. Azadeh Kermansaravi",
        "role": "Postdoctoral researcher (alumni)",
        "project": "HARMONY",
        "type": "postdoc",
        "status": "legacy",
        "years": "2024–2025",
        "bio": "Former postdoctoral researcher on HARMONY (WP3), contributing to AI optimisation and software implementation within the Harmony mathematical framework.",
        "keywords": ["AI optimisation", "Harmony toolbox"],
        "links": [("Project", "projects/harmony.html")],
    },
    {
        "slug": "ajay-shetgaonkar",
        "name": "Dr. Ajay Shetgaonkar",
        "role": "PhD graduate · Postdoc alumni",
        "project": "InterOPERA / SectorPlan",
        "type": "phd",
        "status": "legacy",
        "years": "PhD 2020–2024 · Postdoc 2024–2025",
        "bio": "PhD graduate (21 October 2024) on SectorPlan research in MMC-based MTDC control and protection, including model predictive control. Continued as InterOPERA postdoctoral researcher (2024–2025).",
        "keywords": ["MPC", "MMC", "MTDC protection"],
        "links": [("Project", "projects/interopera.html")],
    },
    {
        "slug": "le-liu",
        "name": "Dr. Le Liu",
        "role": "PhD graduate (alumni)",
        "project": "CSC",
        "type": "phd",
        "status": "legacy",
        "years": "2020–2024",
        "bio": "PhD graduate (22 January 2024, cum laude) on CSC funding. Research on robust traveling-wave protection and control interoperability for multiterminal DC grids.",
        "keywords": ["Traveling-wave protection", "MTDC", "Cum laude"],
        "links": [],
    },
    {
        "slug": "debottam-mukherjee",
        "name": "Dr. Debottam Mukherjee",
        "role": "Postdoctoral researcher (alumni)",
        "project": "HARMONY",
        "type": "postdoc",
        "status": "legacy",
        "years": "2024",
        "bio": "Former postdoctoral researcher contributing to the HARMONY project on harmonic stability assessment of PE-penetrated power systems.",
        "keywords": ["HARMONY", "Harmonic stability"],
        "links": [("Project", "projects/harmony.html")],
    },
    {
        "slug": "rashmi-prasad",
        "name": "Dr. Rashmi Prasad",
        "role": "Postdoctoral researcher (alumni)",
        "project": "BiGER Explore",
        "type": "postdoc",
        "status": "legacy",
        "years": "2023–2024",
        "bio": "Former postdoctoral researcher on BiGER Explore, focusing on power system stability and control challenges of converter-interfaced devices in large networks.",
        "keywords": ["Converter-driven stability", "BiGER"],
        "links": [("Project", "projects/biger-explore.html")],
    },
    {
        "slug": "dongyu-li",
        "name": "Dr. Dongyu Li",
        "role": "Postdoctoral researcher (alumni)",
        "project": "HARMONY",
        "type": "postdoc",
        "status": "legacy",
        "years": "2023–2024",
        "bio": "Former postdoctoral researcher on the HARMONY project.",
        "keywords": ["HARMONY"],
        "links": [("Project", "projects/harmony.html")],
    },
    {
        "slug": "sounak-nandi",
        "name": "Dr. Sounak Nandi",
        "role": "Postdoctoral researcher (alumni)",
        "project": "HARMONY",
        "type": "postdoc",
        "status": "legacy",
        "years": "2023–2024",
        "bio": "Former postdoctoral researcher on the HARMONY project.",
        "keywords": ["HARMONY"],
        "links": [("Project", "projects/harmony.html")],
    },
    {
        "slug": "vaibhav-nougain",
        "name": "Dr. Vaibhav Nougain",
        "role": "Postdoctoral researcher (alumni)",
        "project": "SUNRISE",
        "type": "postdoc",
        "status": "legacy",
        "years": "2023–2025",
        "bio": "Former postdoctoral researcher on SUNRISE, contributing to control, operation and protection research for RES integration using real-time simulation platforms.",
        "keywords": ["SUNRISE", "RTS", "Protection"],
        "links": [("Project", "projects/sunrise.html")],
    },
]

MSC_ALUMNI = [
    {"name": "Jane Marchand", "year": "2021", "title": "EMT model and dynamic power management strategy of an offshore renewable energy hub with local power-to-gas conversion", "note": ""},
    {"name": "Milan Jankovski", "year": "2022", "title": "Developing and testing a novel busbar protection scheme for impedance-earthed distribution networks", "note": "cum laude"},
    {"name": "Morteza Aghahadi", "year": "2022", "title": "Sliding mode control of the hybrid power systems with power electronics incorporated", "note": "Politecnico di Milano · cum laude"},
    {"name": "Shivesh Choudhary", "year": "2022", "title": "A review of Smart Protection solutions for Future Power Systems", "note": ""},
    {"name": "Utkarsh Singh", "year": "2023", "title": "Comparative analysis of Grid forming and Grid following controls for Type-3 and Type-4 Wind Turbines", "note": "cum laude"},
    {"name": "Sankarshan Durgaprasad", "year": "2023", "title": "Energy Efficient Operation of Vessels: Analysis of Potential Hybrid Solutions with Li-Ion Battery System", "note": ""},
    {"name": "Rohan Kamat Tarcar", "year": "2023", "title": "Revolutionising MTDC Networks: Unlocking the Power of FPGA-based MMCs with Grid Forming Control on RSCAD through Model Predictive Control", "note": "cum laude"},
    {"name": "Matthijs Mosselaar", "year": "2023", "title": "Analysis and Modeling of the Hybrid Vessel's Electrical Power System", "note": ""},
    {"name": "Jeroen van Ammers", "year": "2023", "title": "Condition Monitoring of MMC Submodule Semiconductors", "note": "cum laude · 10/10"},
    {"name": "Vishnu Sai Nair", "year": "2023", "title": "Protection Study of MTDC Power System", "note": ""},
    {"name": "Bara Masalmeh", "year": "2024", "title": "Neural Network-Based Predictive Control for Modular Multilevel Converters in HVDC Transmission Grids", "note": ""},
    {"name": "Rahul Rane", "year": "2024", "title": "Transfer Learning Framework for Impedance Characterization of Modular Multilevel Converters", "note": "cum laude"},
    {"name": "Najeein Cherat", "year": "2024", "title": "MMC Control in HVDC System connected to Offshore Wind Farms", "note": ""},
    {"name": "Fajril Fajril Mardiansah", "year": "2025", "title": "On Performance and Compliance of Grid-Forming Assets", "note": ""},
    {"name": "Tejas Kunbi", "year": "2025", "title": "Development of grid code compliance tool for GFM technology", "note": ""},
]

PROJECTS = [
    {
        "slug": "interopera",
        "name": "InterOPERA",
        "full_name": "Enabling Interoperability of Multi-Vendor HVDC Grids",
        "status": "Current",
        "years": "2023–2027",
        "role": "Co-lead from TU Delft",
        "funder": "Horizon Europe · Grant 101095874 · CL5-2022-D3-01-09",
        "summary": "Unlocking multi-vendor, multi-terminal, multi-purpose HVDC grids with grid-forming capability for large-scale offshore wind integration.",
        "overview": "Acceleration of offshore wind is central to Europe’s climate-neutrality goal for 2050. Multi-terminal HVDC systems can interconnect Member States and wind farms cost-effectively, but today’s HVDC systems from different suppliers are not interoperable: a converter from vendor A cannot simply connect to a station from vendor B because of proprietary specifications and standards.",
        "description": "InterOPERA proposes a coordinated approach across industry and academia to achieve multi-terminal, multi-vendor, multi-purpose HVDC systems with grid-forming control. The project develops functional and technical integration frameworks, a real-time physical demonstrator, guidance for coordinated European grid architecture and planning, and pathways for multi-vendor procurement.\n\nAfter defining minimum requirements for standardised interaction studies and interfaces, a demonstrator is built from models of different vendors. Offline and real-time simulations investigate component interactions; minimum requirements for control and protection cubicles are defined, including ancillary services. Outcomes support a stepwise verification process for new vendors and harmonised recommendations for European connection network codes.",
        "objectives": [
            "Functional, technical integration and validation frameworks for modular, interoperable control and protection",
            "Real-time physical demonstrator of multi-vendor multi-terminal HVDC with grid-forming capability",
            "Guidance for coordinated European HVDC grid architecture and topology",
            "Procurement pathways for multi-vendor HVDC projects and offshore energy development",
        ],
        "partners": "TSOs (TenneT NL/DE, RTE, Amprion, Energinet, 50Hertz, Terna, Statnett); HVDC vendors (Siemens Energy, Hitachi Energy); DC breaker manufacturers (SCiBreak); wind partners (GE, Ørsted, Vestas, Siemens Gamesa, Equinor); associations (SuperGrid, T&D Europe, WindEurope, Vattenfall); academia (TU Delft, University of Groningen).",
        "tud_role": "TU Delft co-leads academic contributions, including offline and real-time SIL/HIL interaction studies of the multi-vendor demonstrator in PSCAD/EMTDC and RSCAD/RTDS, supporting future multi-vendor HVDC grid projects.",
        "official": "https://interopera.eu/",
        "tud": "https://www.tudelft.nl/protection-centre/ongoing-projects/interopera-1",
        "cordis": "https://cordis.europa.eu/project/id/101095874",
        "people": ["rohan-kamat-tarcar", "arjita-pal", "aleksandra-lekic", "farzad-dehghan-marvasti", "reza-bakhshi-jafarabadi", "ajay-shetgaonkar", "marjan-popov", "remko-koornneef"],
        "image": "projects/interopera-card.jpg",
        "logo": "projects/interopera.svg",
    },
    {
        "slug": "inter-open",
        "name": "Inter-oPEn",
        "full_name": "Interoperability of the Power Electronics dominated grid by openness",
        "status": "Current",
        "years": "2024–2028 (1 June 2024 – 31 May 2028)",
        "role": "PI from TU Delft · WP4 lead",
        "funder": "Horizon Europe MSCA Doctoral Network · Grant 101119349",
        "summary": "MSCA doctoral network integrating electrical engineering and legal research on PE-asset interoperability through openness.",
        "overview": "Inter-oPEn is a doctoral programme that gathers electrical engineering and legal researchers. Fellows study safe and reliable operation of PE-dominated power systems and gain expertise through academic and industrial secondments. Openness is central — spanning control, protection, interoperability, governance and intellectual property.",
        "description": "Power-electronic devices enable renewable integration, but interoperability faces technical, IP and regulatory barriers. Inter-oPEn trains 10 researchers across 8 academic and 13 industrial associated partners, combining engineering and legal perspectives and making openness a foundation of research and training.\n\nAt TU Delft, research focuses on grid-forming offshore wind farms with MMC-based HVDC: how GFM OWFs establish voltage and frequency; fault-tolerant control under internal submodule faults; and validation with Power Hardware-in-the-Loop under realistic delays and hardware limits.",
        "objectives": [
            "Technical and legal training for future PE-dominated systems",
            "Industry–academia collaboration and mobility (secondments)",
            "Innovation-oriented research and practical engineering solutions",
            "Scientific and transferable skills development",
            "TU Delft focus: GFM control for OWFs in MMC-HVDC; submodule fault-tolerant MMC control; PHIL validation platform",
        ],
        "partners": "Academic: RWTH, KU Leuven, RUG, KIT, TU Braunschweig, UPC, TU Delft, KTH. Industrial/associated: ETH Zurich, 50Hertz, Ostfalia, SVK, Siemens Energy, PTB, SSNET-T, TransnetBW, ELIA, Mosaic, CRESYM and others.",
        "tud_role": "Aleksandra Lekić is PI from TU Delft and WP4 lead. Doctoral candidate Tuanku Badzlin Hashfi works on GFM MMC-HVDC control, internal MMC faults and PHIL validation.",
        "official": "https://inter-open.eu/",
        "tud": None,
        "alt": "https://inter-open.eonerc.rwth-aachen.de/",
        "people": ["tuanku-badzlin-hashfi", "aleksandra-lekic"],
        "image": "projects/inter-open-card.jpg",
        "logo": "projects/inter-open.png",
    },
    {
        "slug": "mitigate-harm",
        "name": "MITIGATE-HARM",
        "full_name": "MITIGATE HARMonics in power electronics-based power systems",
        "status": "Current",
        "years": "2026–2029",
        "role": "Project coordinator · WP lead",
        "funder": "CETP Joint Call 2024 (CETP-2024-00024) · TU Delft funded by NWO",
        "summary": "Fast, open-source tools to identify, assess and mitigate converter-driven instabilities and harmonic resonances in hybrid AC/DC and multi-vendor HVDC grids.",
        "overview": "MITIGATE-HARM makes future power systems more resilient by tackling converter-driven instabilities and harmonic resonances that vendor-specific tools cannot assess quickly enough. It builds on two open-source platforms — Harmony (impedance-based) and DPsim (eigenvalue-based) — to support TSOs already at early planning stages and enable safe integration of up to 100% renewables.",
        "description": "Digitalisation and RES integration have sharply increased PE penetration. Converters introduce fast dynamics and can behave as negative resistance over wide frequencies, risking oscillations and blackouts — especially in hybrid AC/DC and multi-terminal multi-vendor HVDC systems, aggravated by limited standardisation and vendor-specific projects.\n\nMITIGATE-HARM develops a unified mathematical framework for converter-driven stability assessment: extending Harmony (C++) for instability/resonance identification, mitigation and wideband passivity; extending DPsim for hybrid AC/DC eigenvalue analysis and OPAL-RT integration. Developments are cross-validated on IEEE 9-bus + HVDC and Nordic PE benchmarks against PSCAD, Z-tool and OPAL-RT, then applied to TenneT large-scale cases. Target KPIs include <1% inaccuracy vs commercial tools, order-of-magnitude faster simulation (minutes→seconds), and >30% reduction of identified instabilities via mitigation measures.",
        "objectives": [
            "Advanced Harmony toolbox: instability/resonance ID, mitigation, wideband passivity (open-source C++)",
            "Enhanced DPsim: hybrid AC/DC modelling, eigenvalue analysis, OPAL-RT integration",
            "Open benchmarks and public datasets via CRESYM Collaborative Dynamic Library (CoLib)",
            "Verification and application on real-life TenneT cases; pan-European scalability analysis",
            "Dissemination: open-access papers, workshops, training; long-term LF Energy maintenance path",
        ],
        "partners": "Coordinator: TU Delft (NL). Partners: AUTH (GR), RWTH Aachen (DE), TenneT TSO GmbH (DE), OPAL-RT Germany GmbH (DE), CRESYM (BE).",
        "tud_role": "TU Delft coordinates the project. Team includes Aleksandra Lekić, Hao Xu, Muhammad Noman Ashraf and Robert Dimitrovski (TenneT / part-time TU Delft).",
        "official": "https://mitigate-harm.eu/",
        "tud": "https://www.tudelft.nl/en/2026/eemcs/building-more-resilient-and-reliable-power-systems-for-the-future",
        "nwo": "https://www.nwo.nl/en/projects/ep160224002",
        "people": ["hao-xu", "muhammad-noman-ashraf", "aleksandra-lekic", "robert-dimitrovski"],
        "image": "projects/mitigate-harm-card.jpg",
        "logo": "projects/mitigate-harm-full.png",
        "related_portfolio": ["harmony-toolbox", "dqsym", "acdc-opflow"],
    },
    {
        "slug": "harmony",
        "name": "HARMONY",
        "full_name": "MatHematicAl fRamework for harMONic stabilitY assessment of power electronics-based power systems",
        "status": "Current",
        "years": "2023–2026",
        "role": "Principal investigator",
        "funder": "CRESYM (TU Delft, TenneT, Swissgrid)",
        "summary": "Open-source mathematical framework for harmonic stability assessment of PE-penetrated hybrid AC/DC systems — OPF, dynamic phasors and impedance methods in seconds on general-purpose CPUs.",
        "overview": "Massive PE penetration (PV, wind, batteries, HVDC, STATCOMs) can cause resonance and harmonic interactions that local mitigation cannot fully prevent. HARMONY develops a comprehensive, user-friendly open-source tool to simulate hybrid power system components for stability assessment much faster than commercial EMT workflows.",
        "description": "HARMONY (“HARMONic stabilitY assessment of PE-penetrated power systems”) builds models for hybrid power systems and dynamic-phasor components (WP1), optimisation models for harmonic and DP analysis of AC–DC systems (WP2), and implements/tests the mathematical framework (WP3).\n\nMilestones include experimental validation of spectral and DP converter models in the RTDS laboratory, interconnection of spectral/DP/power-flow models, and full-framework experimental validation. By-products include the ACDC-OpFlow toolbox and DQsym dynamic-phasor library, feeding the C++ Harmony framework.",
        "objectives": [
            "WP1: HPS and dynamic-phasor component models",
            "WP2: Optimisation models for harmonic and DP analysis of AC–DC systems",
            "WP3: Framework implementation, RTDS testing and open-source release",
            "Deliverables include AC/DC OPF toolbox, DQsym, Harmony code/docs, and peer-reviewed publications",
        ],
        "partners": "Common CRESYM project by TU Delft, TenneT and Swissgrid.",
        "tud_role": "Aleksandra Lekić is PI. TU Delft leads mathematical framework design, component spectral models, harmonic stability solver, toolbox architecture and funding acquisition, with PhD/postdoc contributions on OPF, DQsym and software.",
        "official": "https://cresym.eu/harmony/",
        "tud": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/current-projects/harmony",
        "github": "https://github.com/CRESYM/Harmony",
        "docs": "https://cresym.github.io/Harmony-Doc/",
        "people": ["saif-alsarayreh", "haixiao-li", "aleksandra-lekic", "robert-dimitrovski", "azadeh-kermansaravi", "debottam-mukherjee", "dongyu-li", "sounak-nandi"],
        "image": "projects/harmony-card.jpg",
        "logo": "projects/harmony-cresym.png",
        "related_portfolio": ["harmony-toolbox", "acdc-opflow", "dqsym"],
    },
    {
        "slug": "prosecco",
        "name": "PROSECCO",
        "full_name": "DC Protection, Security, Control and Optimisation",
        "status": "Current",
        "years": "2024–2028 (1 July 2024 – 30 June 2028)",
        "role": "PI from TU Delft · WP4 lead",
        "funder": "Horizon Europe · Grant 101160687",
        "summary": "Maturing hybrid AC/DC grids through DC protection near converters and congestion management — with four European demonstrators.",
        "overview": "Meshed HVDC is key to integrate offshore wind and upgrade the European power system. PROSECCO advances grid protection near HVDC converters and congestion management for hybrid AC/DC grids using model-based systems engineering with a vendor-neutral design approach.",
        "description": "The project advances harmonised protection specifications, improved testing, multi-vendor integration, grid stability and selective protection. In congestion management it develops power-flow schedulers, power-flow control hardware and holistic cost–benefit tools.\n\nFour demonstrators across three EU member states: (1) unique test equipment for DC relays; (2) DC protection relays in actual DC grids; (3) a full-scale DC power-flow controller; (4) software to evaluate cost-effectiveness of protection and congestion solutions. The project also contributes to standardisation and ENTSO-E recommendations.",
        "objectives": [
            "Unique test equipment for DC relays",
            "DC protection relays installed in actual DC grids",
            "Full-scale DC power-flow controller demonstrator",
            "Cost-effectiveness evaluation software for protection and congestion management",
            "TU Delft WP4: design and demonstration of DC relay and C&P units in RTDS HIL, continued toward DC substation demonstration",
        ],
        "partners": "TU Delft, KU Leuven, TU Braunschweig, TenneT, RTE, UPC, Grenoble INP, ENSAM, Centrale Lille, Université Grenoble Alpes, AMVALOR and others.",
        "tud_role": "TU Delft leads WP4 and the demonstration of DC relay and control & protection units in the hardware-in-the-loop RTDS laboratory, with continuation toward DC substation demonstration. Team: Aleksandra Lekić, Victor Daniel Reyes Dreke, Rahul Rane.",
        "official": "https://prosecco-project.be/",
        "tud": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/current-projects/prosecco",
        "cordis": "https://cordis.europa.eu/project/id/101160687",
        "people": ["rahul-rane", "victor-reyes-dreke", "aleksandra-lekic", "remko-koornneef"],
        "image": "projects/prosecco-card.jpg",
        "logo": "projects/prosecco.svg",
        "related_portfolio": ["hierarchical-cp", "pacs", "hvdc-rtds-models"],
    },
    {
        "slug": "safe-grid",
        "name": "SAFE-GRID",
        "full_name": "Smart and Flexible Control for a Power Electronics-based Electrical Grid",
        "status": "Current",
        "years": "2024–2027",
        "role": "Principal investigator (individual NWO Veni)",
        "funder": "NWO Veni (AES / TTW) · supported by TenneT, GE, The National HVDC Centre",
        "summary": "Standardised microsecond-scale adaptive MPC for PE converters in forthcoming multi-terminal HVDC grids.",
        "overview": "Offshore wind (including North Sea plans toward hundreds of GW) will be transmitted onshore via multi-terminal HVDC and PE converters that must stay stable, reliable and flexible. Converter control remains a bottleneck: millisecond-class responses are too slow for unforeseen disruptions.",
        "description": "SAFE-GRID advances fundamental standardised smart PE controls for HVDC-based grids. It develops adaptive Model Predictive Control combining model-driven and data-driven approaches for real-time converter control with many parameters, guaranteeing stable operation under unforeseen disturbances, faster fault elimination, and smaller voltage/power overshoots — critical in low-inertia PE grids.\n\nResults target TSOs and PE manufacturers: novel comprehensive smart control, an open-access control-unit prototype and HVDC library in RTDS, and increased industry awareness of high-performance smart PE controllers.",
        "objectives": [
            "Novel comprehensive smart control for PE-based power systems",
            "Open-access control-unit prototype for PE converters and HVDC RTDS library",
            "Increase awareness among vendors and utilities of high-performance smart PE control",
        ],
        "partners": "Individual NWO Veni grant with support from TenneT (NL), General Electric (UK), The National HVDC Centre (UK).",
        "tud_role": "Aleksandra Lekić is the Veni PI. Postdoctoral researcher Sunny Singh contributes MPC and ML-driven MMC control research within SAFE-GRID.",
        "official": None,
        "tud": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/current-projects/safe-grid",
        "people": ["sunny-singh", "aleksandra-lekic"],
        "image": "projects/safe-grid-card.jpg",
        "logo": "projects/nwo.jpg",
        "related_portfolio": ["rtds-nn-models", "hierarchical-cp", "hvdc-rtds-models"],
    },
    {
        "slug": "sunrise",
        "name": "SUNRISE",
        "full_name": "Setting Up green eNergy Research In SErbia",
        "status": "Completed",
        "years": "2023–2025",
        "role": "PI from TU Delft · WP3 lead",
        "funder": "Horizon Europe WIDERA · Grant 101079200",
        "summary": "Building research capacity in Serbia and the region for RES integration using real-time simulation (OPAL-RT, RTDS), MOOC training and hybrid AC/DC studies.",
        "overview": "Serbia’s decarbonisation roadmap requires stronger research capacity on control, operation and protection of PE-interfaced renewables and storage. SUNRISE bridges infrastructure and skills gaps by realising RES integration studies on RTS platforms and open training.",
        "description": "The project unlocks hybrid AC/DC simulation across voltage levels (LV microgrids to MV and multi-terminal HVDC), with objectives on robust control for RES integration, reliable operation under disturbances and islanding, and secure selective protection including MT-HVDC.\n\nA MOOC provides guidelines for OPAL-RT/RTDS co-simulation. TU Delft contributed as WP3 lead and to open model libraries and teaching material aligned with the IEEE IES MOOC on HVDC/AC control and protection.",
        "objectives": [
            "Robust control for RES integration (PI, sliding-mode, MPC, Lyapunov methods)",
            "Reliable operation under load transients, islanding and anti-islanding schemes",
            "Secure, selective protection and fault location for MT-HVDC and hybrid systems",
            "Training and RTS capacity building; open libraries and MOOC material",
        ],
        "partners": "University of Belgrade (Serbia); TU Delft (Netherlands); Universidad de Sevilla; Universidad del País Vasco; Poslovno-tehnološki inkubator tehničkih fakulteta, Belgrade.",
        "tud_role": "Aleksandra Lekić: PI from TU Delft and WP3 lead. TU Delft team also includes Vaibhav Nougain and Aditya Shekhar (as listed on the official TU Delft SUNRISE page).",
        "official": None,
        "tud": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/completed-projects/sunrise",
        "github": "https://github.com/control-protection-grids-tudelft/SUNRISE_MPC",
        "people": ["aleksandra-lekic", "vaibhav-nougain", "aditya-shekhar"],
        "image": "projects/sunrise-card.jpg",
        "logo": "projects/sunrise-picture.jpg",
        "related_portfolio": ["sunrise-mpc", "ieee-ies-mooc", "hvdc-rtds-models"],
    },
    {
        "slug": "biger-explore",
        "name": "BiGER Explore",
        "full_name": "Bridging the Gap between EMT and RMS – Explore",
        "status": "Completed",
        "years": "2023–2024",
        "role": "Lead from TU Delft",
        "funder": "CRESYM",
        "summary": "Open use-cases and state-of-the-art methods to bridge EMT and RMS for converter-driven stability in PE-rich grids.",
        "overview": "PE-based components introduce fast dynamics that interact with classical slow electromechanical modes and among converters themselves. Converter-driven stability (e.g. PLL or control gains) can appear before traditional issues, especially in weak networks — requiring more than classical phasor studies, while full long-term EMT remains computationally prohibitive.",
        "description": "BiGER–Explore builds and shares open-source benchmarks illustrating the need for more detailed simulations, and a state-of-the-art review of methods that approach EMT fidelity with better scalability, robustness, transparency and flexibility for network operators and stakeholders.",
        "objectives": [
            "Build and share open-source use cases and benchmarks needing beyond-RMS simulation",
            "State-of-the-art of methods bridging EMT and RMS for converter-driven stability",
        ],
        "partners": "TU Delft, RWTH Aachen and RTE under the CRESYM organisation.",
        "tud_role": "TU Delft lead with Pedro P. Vergara Barrios, Aleksandra Lekić and Rashmi Prasad contributing expertise on converter-interfaced device stability in large networks.",
        "official": None,
        "tud": "https://www.tudelft.nl/ewi/over-de-faculteit/afdelingen/electrical-sustainable-energy/intelligent-electrical-power-grids-iepg-group/projects/completed-projects/biger-explore",
        "github": "https://github.com/CRESYM/BiGER",
        "people": ["aleksandra-lekic", "rashmi-prasad", "pedro-vergara"],
        "image": "projects/biger-explore-card.jpg",
        "logo": "projects/cresym-biger.png",
        "related_portfolio": ["biger"],
    },
    {
        "slug": "easy-res",
        "name": "EASY-RES",
        "full_name": "Enable Ancillary Services by Renewable Energy Sources",
        "status": "Completed",
        "years": "2018–2021",
        "role": "Task 6.4 lead",
        "funder": "Horizon 2020 · Grant 764090",
        "summary": "Making distributed RES grid-friendly providers of ancillary services — virtual inertia, frequency support, harmonics filtering and viable business models.",
        "overview": "From Aleksandra Lekić’s LinkedIn project record (Jan 2018 – Dec 2021): EASY-RES increases power-system robustness to abrupt frequency changes and enables high RES penetration without grid reinforcement, while preserving long-term security and developing AS business models.",
        "description": "Key objectives: introduce virtual inertia and damping in DRES; provide frequency-dependent active power; raise LV and MV renewable penetration while avoiding reinforcement investment; make RES more grid-friendly by reducing short-term power fluctuations at DRES and HV/MV substation level and introducing active harmonics filtering in each DRES converter; preserve long-term grid security under very large DRES penetration by reducing reserve needs after fault recovery; develop viable stakeholder business models via new metrics for quantifying ancillary services and evaluating economic cost and benefit.",
        "objectives": [
            "Virtual inertia and damping in DRES for frequency robustness",
            "Frequency-dependent active power for grid stability",
            "Higher LV/MV RES penetration without reinforcement",
            "Reduced short-term fluctuations and active harmonic filtering per DRES converter",
            "Lower post-fault reserve requirements; AS metrics and cost–benefit business models",
        ],
        "partners": "European H2020 consortium (see CORDIS and project site). TU Delft contribution within Task 6.4.",
        "tud_role": "Aleksandra Lekić led Task 6.4. Work linked to converter control for renewables providing ancillary services (also reflected in later TU Delft innovation-project summaries).",
        "official": "https://www.easyres-project.eu/",
        "tud": "https://www.tudelft.nl/en/innovatie-impact/innovation-projects/projects-2022/easy-res",
        "cordis": "https://cordis.europa.eu/project/id/764090",
        "people": ["aleksandra-lekic"],
        "image": "projects/easy-res-card.jpg",
        "logo": "projects/easy-res.png",
    },
]

PORTFOLIO = [
    {
        "slug": "harmony-toolbox",
        "name": "Harmony toolbox",
        "kind": "Software · Open source",
        "category": "Software",
        "trl": "TRL 3–4",
        "summary": "C++ framework for dynamic-phasor time-domain simulation, AC/DC OPF and harmonic stability assessment of PE-penetrated AC/MTDC systems.",
        "description": "Harmony is the flagship open-source mathematical framework of the Interoperability Program and the HARMONY / MITIGATE-HARM research line. It targets converter-driven and harmonic stability studies that commercial EMT tools handle slowly and expensively.\n\nThe toolbox interconnects component modelling, operating-point setup via AC/DC OPF, and impedance-based harmonic stability assessment, aiming for execution in seconds on general-purpose CPUs. Documentation and releases are curated with TU Delft Digital Competence Centre support.",
        "status_plans": [
            "Satisfies TRL 3–4 for software; funded via industrial HARMONY and MITIGATE-HARM",
            "Supports GFM-related control studies and stability indices aligned with ENTSO-E and AEMO guidance",
            "Validated on realistic European grid cases including a Slovenian network study",
        ],
        "github": "https://github.com/CRESYM/Harmony",
        "docs": "https://cresym.github.io/Harmony-Doc/",
        "related": ["harmony", "mitigate-harm"],
        "image_tone": 0,
    },
    {
        "slug": "acdc-opflow",
        "name": "ACDC-OpFlow",
        "kind": "Software · Open source",
        "category": "Software",
        "trl": "TRL 4–5",
        "summary": "Unified cross-language AC/DC optimal power flow framework in C++, Julia, Python and MATLAB.",
        "description": "ACDC-OpFlow provides a beginner-friendly, cross-language OPF stack for hybrid AC / VSC-MTDC grids, with a unified modelling structure and Gurobi as a consistent solver backend. It is a HARMONY by-product and a building block for hierarchical grid controllers.\n\nThe library supports researchers who prefer MATLAB, Python, Julia or C++ while sharing the same OPF formulation for AC/DC systems.",
        "status_plans": [
            "Open-source software at TRL 4–5",
            "Used with hierarchical AC/DC grid control studies in the group",
        ],
        "github": "https://github.com/CRESYM/ACDC_OPF",
        "docs": "https://research.tudelft.nl/en/datasets/acdc-opflow-unified-cross-language-framework-for-acdc-optimal-pow/",
        "related": ["harmony"],
        "image_tone": 1,
    },
    {
        "slug": "dqsym",
        "name": "DQsym",
        "kind": "Software · Open source",
        "category": "Software",
        "trl": "TRL 4–5",
        "summary": "MATLAB/Simulink dynamic-phasor library for hybrid AC/DC systems with state-space and harmonic-aware simulation.",
        "description": "DQsym represents nearly periodic signals via time-varying Fourier coefficients in a DQ frame, capturing converter dynamics that static phasors miss without full EMT switching resolution. It supports eigenvalue-based small-signal analysis and impedance-oriented harmonic assessment in one environment.\n\nDeveloped under HARMONY with open release via the control-protection-grids-tudelft organisation.",
        "status_plans": [
            "Open-source MATLAB/Simulink library at TRL 4–5; funded via industrial HARMONY",
            "Supports interchangeable stability assessment between time-domain and harmonic simulation",
        ],
        "github": "https://github.com/control-protection-grids-tudelft/DP",
        "docs": None,
        "related": ["harmony", "mitigate-harm"],
        "image_tone": 2,
    },
    {
        "slug": "hvdc-rtds-models",
        "name": "HVDC RTDS models",
        "kind": "Software · RSCAD/RTDS library",
        "category": "Software",
        "trl": "One-of-a-kind library",
        "summary": "Scripted North-Sea energy hub and HVDC grid models for RSCAD/RTDS (±525 kV / 2 GW class, CIGRE B4 / TenneT-aligned).",
        "description": "An open RSCAD/RTDS model library of futuristic multi-terminal HVDC / energy-hub systems with ratings aligned to 2 GW, ±525 kV designs and adjusted CIGRE B4 parameters based on TenneT substation and cable practice. Built for NovaCor 1.0 and used in teaching, research and neural-network control libraries.\n\nReferenced in CIGRE B4 contexts and EU project PROSECCO interaction and protection studies.",
        "status_plans": [
            "Open library used in teaching and neural-network control research",
            "Applied in PROSECCO interaction and protection studies",
        ],
        "github": "https://github.com/control-protection-grids-tudelft/HVDC-RTDS-models",
        "docs": None,
        "related": ["prosecco", "safe-grid", "sunrise"],
        "image_tone": 3,
    },
    {
        "slug": "rtds-nn-models",
        "name": "RTDS neural-network libraries",
        "kind": "Software · RSCAD/RTDS",
        "category": "Software",
        "trl": "One-of-a-kind library",
        "summary": "Real-time trainable neural-network models for advanced HVDC converter control on RTDS — advertised by RTDS Technologies worldwide.",
        "description": "Open neural-network control libraries for RSCAD/RTDS enabling real-time training and adaptive HVDC converter control on NovaCor 1.0 platforms. Demonstrated for adaptive PI MMC control and tightly linked to the group’s machine-learning-in-the-loop research narrative.",
        "status_plans": [
            "Open libraries highlighted by RTDS Technologies",
            "Used for adaptive MMC control studies on RTDS",
        ],
        "github": "https://github.com/control-protection-grids-tudelft/RTDS_NN_models",
        "docs": None,
        "related": ["safe-grid"],
        "image_tone": 0,
    },
    {
        "slug": "sunrise-mpc",
        "name": "SUNRISE MPC (RTDS)",
        "kind": "Software · RSCAD/RTDS",
        "category": "Software",
        "trl": "Library",
        "summary": "Adaptive deadbeat MPC control models for HVDC converters, developed in the SUNRISE programme.",
        "description": "Companion RTDS library demonstrating adaptive deadbeat model predictive control for MMC/HVDC converters, produced in the SUNRISE capacity-building and control research line. Complements the NN libraries and HVDC hub models for teaching and HIL experiments.",
        "status_plans": [
            "Open models for adaptive deadbeat MPC on RTDS",
            "Used in SUNRISE teaching and HIL experiments",
        ],
        "github": "https://github.com/control-protection-grids-tudelft/SUNRISE_MPC",
        "docs": None,
        "related": ["sunrise"],
        "image_tone": 1,
    },
    {
        "slug": "ieee-ies-mooc",
        "name": "IEEE IES MOOC model library",
        "kind": "Training · Open source",
        "category": "Training",
        "trl": "Courseware · 74 PDH (≈3 ECTS)",
        "summary": "RSCAD/RTDS and MATLAB libraries for the IEEE IES MOOC on control and protection of HVDC/AC electrical grids.",
        "description": "Aleksandra Lekić is responsible instructor and teaches about one third of the IEEE IES MOOC “Control and protection of HVDC/AC electrical grids”, co-financed by SUNRISE and IEEE IES, with 15 lecturers from academia and industry.\n\nThe free Resource Center course is backed by open RSCAD/RTDS and MATLAB model libraries. Completing the course and end quiz yields 74 PDH (≈3 ECTS). The material fills a gap seldom covered at universities at this depth for both academia and industry.",
        "status_plans": [
            "Listed in Open Sustainable Technology GitHub ecosystem topics",
            "Complements EE4545 (Electrical Power Systems of the Future) RTDS HIL practicals; PAO offering from 2026",
        ],
        "github": "https://github.com/control-protection-grids-tudelft/Control-and-protection-of-HVDC-AC-electrical-grids-IEEE-IES-MOOC",
        "docs": "https://resourcecenter.ies.ieee.org/education/control-and-protection-hvdcac-electrical-grids",
        "related": ["sunrise"],
        "image_tone": 2,
    },
    {
        "slug": "biger",
        "name": "BiGER benchmarks",
        "kind": "Software · Open source",
        "category": "Software",
        "trl": "Benchmarks",
        "summary": "Open use-cases and benchmarks bridging EMT and RMS for converter-driven stability studies.",
        "description": "Public BiGER Explore outcomes: shared use cases and open-source benchmarks that show when classical RMS/phasor tools are insufficient for converter-driven stability, plus curated state-of-the-art methods aiming for EMT-like insight without full EMT cost.",
        "status_plans": [
            "Open repository under CRESYM/BiGER",
            "Supports operators and researchers comparing modelling domains for PE-rich grids",
        ],
        "github": "https://github.com/CRESYM/BiGER",
        "docs": None,
        "related": ["biger-explore"],
        "image_tone": 1,
    },
    {
        "slug": "hierarchical-cp",
        "name": "Hierarchical control & protection",
        "kind": "Software · Research",
        "category": "Software",
        "trl": "Research software",
        "summary": "Centralized/decentralized hierarchical C&P in C++/Julia for offline and real-time targets (FPGA, GTSOC 2.0, MCU), integrating AC/DC OPF and adaptive MPC.",
        "description": "Integration of hierarchical control, protection and fault-location concepts from SAFE-GRID, PROSECCO and HARMONY into deployable toolboxes.\n\nHierarchical control (C++/Julia) covers centralized and decentralized schemes including AC/DC OPF (via ACDC-OpFlow) and decentralized PI/MPC (robust and adaptive variants), easily deployed to FPGA, GTSOC 2.0 or microcontrollers. Hierarchical protection addresses HVDC fault detection and location with the same real-time target flexibility.",
        "status_plans": [
            "Control and protection toolboxes for offline and real-time targets",
            "Builds on SAFE-GRID, PROSECCO, HARMONY and InterOPERA research",
            "Further algorithms and integration with PACS and DCGC",
        ],
        "github": None,
        "docs": None,
        "related": ["safe-grid", "prosecco", "interopera", "harmony"],
        "image_tone": 2,
    },
    {
        "slug": "pacs",
        "name": "PACS",
        "kind": "Hardware · Product",
        "category": "Hardware",
        "trl": "PROSECCO demonstrator",
        "summary": "Protection and Control System — hierarchical C&P integrated on FPGA within PROSECCO.",
        "description": "PACS packages hierarchical control and protection on FPGA hardware as part of PROSECCO demonstrator work. It is the hardware embodiment of the Interoperability Program’s C&P software stack for DC relays and converter-near protection/control units in HIL and substation contexts.",
        "status_plans": [
            "FPGA-based hierarchical control and protection within PROSECCO",
            "Demonstrated toward DC relay and converter-near C&P units in HIL",
        ],
        "github": None,
        "docs": None,
        "related": ["prosecco"],
        "image_tone": 3,
    },
    {
        "slug": "dcgc",
        "name": "DC Grid Controller (DCGC)",
        "kind": "Hardware · Product",
        "category": "Hardware",
        "trl": "Concept",
        "summary": "Modular digital-substation concept for interoperable DC grid control (SCADA/EMS/LFC/scheduling functions).",
        "description": "DCGC aims to act as a digital substation / control-centre layer for DC grids: modular provision of SCADA, EMS-like grid calculations, load-frequency control, scheduling and related functions with interoperability by design.\n\nArchitecture builds on the LF Energy SEAPATH open-source substation stack with ACDC-OpFlow integrated — matching the RTDS–Ethernet–SEAPATH laboratory architecture already exercised in the group.",
        "status_plans": [
            "Modular DC grid control concept based on LF Energy SEAPATH",
            "Integrates ACDC-OpFlow for grid calculation functions",
        ],
        "github": None,
        "docs": "https://www.lfenergy.org/projects/seapath/",
        "related": ["harmony"],
        "image_tone": 0,
    },
    {
        "slug": "dcss",
        "name": "DC Switching Station (DCSS)",
        "kind": "Hardware · Product",
        "category": "Hardware",
        "trl": "Concept",
        "summary": "Switchyard controller for IED communication and modular HVDC grid expansion points.",
        "description": "DCSS is a switchyard controller providing communication between IEDs and a modular connection point for expandable multi-terminal HVDC grids — complementing PACS (bay/converter C&P) and DCGC (grid control applications).",
        "status_plans": [
            "Switchyard controller concept for modular multi-terminal HVDC expansion",
            "Complements PACS and DCGC in the Interoperability Program hardware stack",
        ],
        "github": None,
        "docs": None,
        "related": ["interopera", "prosecco"],
        "image_tone": 1,
    },
]

NEWS = [
    {"year": 2026, "date": "2026-01", "title": "Building more resilient and reliable power systems", "body": "TU Delft EEMCS feature on the CETP/NWO MITIGATE-HARM project coordinated by Aleksandra Lekić.", "href": "https://www.tudelft.nl/en/2026/eemcs/building-more-resilient-and-reliable-power-systems-for-the-future"},
    {"year": 2026, "date": "2026-01", "title": "MITIGATE-HARM project website", "body": "Consortium partners launched open-source tools for harmonic and converter-driven instability mitigation.", "href": "https://mitigate-harm.eu/"},
    {"year": 2025, "date": "2025-01", "title": "IEEE IES newsletter — MOOC feature", "body": "IEEE IES featured the MOOC “Control and protection of HVDC/AC electrical grids”.", "href": "https://iten.ieee-ies.org/featured-news/2025/ieee-ies-mooc-control-and-protection-of-hvdc-ac-electrical-grids/"},
    {"year": 2025, "date": "2025-09", "title": "Hackathon on Energy Transition in Buildings", "body": "Two-day 4TU Energy workshop on energy supply & demand in residential buildings.", "href": None},
    {"year": 2024, "date": "2024-11", "title": "Anchoring Power: control & stability in offshore energy hubs", "body": "TU Delft Stories feature on control and stability research for offshore hubs.", "href": "https://www.tudelft.nl/en/stories/articles/anchoring-power-ensuring-control-and-stability-in-offshore-energy-hubs"},
    {"year": 2024, "date": "2024-09", "title": "IEEE IES newsletter — MOOC (September)", "body": "Follow-up feature on the IEEE IES Resource Center short course.", "href": "https://resourcecenter.ies.ieee.org/education/control-and-protection-hvdcac-electrical-grids"},
    {"year": 2024, "date": "2024-06", "title": "First short course in the IEEE IES Resource Center", "body": "IEEE IES announced the HVDC/AC control & protection MOOC as its first Resource Center short course.", "href": "https://iten.ieee-ies.org/featured-news/2024/the-first-short-course-in-ies-resource-center/"},
    {"year": 2024, "date": "2024-10", "title": "RTDS case study: ML for real-time HVDC simulation", "body": "Enhancing real-time HVDC simulation with machine learning in RSCAD/RTDS.", "href": "https://research.tudelft.nl/en/clippings/case-study-machine-learning-tu-delft-is-enhancing-real-time-hvdc-/"},
    {"year": 2023, "date": "2023-08", "title": "Six promising young EEMCS researchers receive Veni grant", "body": "EEMCS feature on Veni laureates including SAFE-GRID (Aleksandra Lekić).", "href": "https://www.tudelft.nl/en/2023/eemcs/six-promising-young-eemcs-researchers-receive-veni-grant-1"},
    {"year": 2023, "date": "2023-08", "title": "NWO Veni grant for SAFE-GRID", "body": "Awarded for Smart and Flexible Control for a Power Electronics-based Electrical Grid.", "href": "https://www.nwo.nl/en/projects/20248"},
    {"year": 2021, "date": "2021-01", "title": "Humans of EEMCS: Aleksandra Lekić", "body": "Profile interview on joining TU Delft and HVDC/AC research.", "href": "https://www.tudelft.nl/en/eemcs/current/humans-of-eemcs/humans-of-eemcs-aleksandra-lekic"},
]

AWARDS = [
    {"year": "2024", "title": "PowerWeb best paper award", "detail": "For the IEEE TPWRD paper on fault location in multi-terminal radial MVDC microgrids (CV paper [35]).", "href": None},
    {"year": "2023", "title": "NWO Veni laureate (AES / TTW)", "detail": "SAFE-GRID: Smart and Flexible Control for a Power Electronics-based Electrical Grid — top ~10% young researchers in applied engineering sciences in the Netherlands.", "href": "https://research.tudelft.nl/en/prizes/veni-grant-aes-2022-5/"},
    {"year": "2021", "title": "Best paper award — Journal of Circuit Theory & Applications", "detail": "For microsecond nonlinear model predictive control for DC–DC converters (2020 paper).", "href": "https://research.tudelft.nl/en/prizes/best-paper-award-in-2020/"},
    {"year": "2019 & 2017", "title": "Professor Mirko Milić awards", "detail": "Best papers in circuit theory, School of Electrical Engineering, University of Belgrade (papers [49] and [53]).", "href": None},
    {"year": "2018", "title": "Best PhD thesis — University of Belgrade", "detail": "Zadužbina Andrejević award.", "href": None},
    {"year": "2018", "title": "Coimbra Group scholarship", "detail": "Scholarship Programme for Young Researchers from the European Neighbourhood.", "href": None},
    {"year": "2013", "title": "Best student of generation", "detail": "School of Electrical Engineering, University of Belgrade (class 2011/2012).", "href": None},
    {"year": "2012", "title": "HUAWEI award", "detail": "Best student of the University of Belgrade in the technical studies.", "href": None},
    {"year": "2012", "title": "Professor Mirko Milić award", "detail": "Best student in the final year, School of Electrical Engineering.", "href": None},
]

COURSES = [
    {
        "kind": "Online / MOOC",
        "name": "Control and protection of HVDC/AC electrical grids",
        "code": "IEEE IES Resource Center",
        "role": "Responsible instructor (~1/3 of the course)",
        "detail": "Free IEEE IES MOOC with 15 lecturers from academia and industry; co-financed by SUNRISE and IEEE IES. Completing the course and end quiz yields 74 PDH (≈3 ECTS). Listed in Open Sustainable Technology. Open RSCAD/RTDS and MATLAB model libraries on GitHub.",
        "href": "https://resourcecenter.ies.ieee.org/education/control-and-protection-hvdcac-electrical-grids",
        "extra": "https://github.com/control-protection-grids-tudelft/Control-and-protection-of-HVDC-AC-electrical-grids-IEEE-IES-MOOC",
    },
    {
        "kind": "MSc · TU Delft",
        "name": "Electrical Power System of the Future",
        "code": "EE4545",
        "role": "Responsible instructor (3 years)",
        "detail": "Core MSc Electrical Power Engineering course on future power systems.",
        "href": None,
        "extra": None,
    },
    {
        "kind": "MSc · TU Delft",
        "name": "Matlab Fundamentals",
        "code": "SET3815-M",
        "role": "Responsible instructor (5 years)",
        "detail": "Foundational MATLAB course for EPE / SET students.",
        "href": None,
        "extra": None,
    },
    {
        "kind": "MSc coordination",
        "name": "Electrical Engineering — Electrical Power Engineering",
        "code": "MSc EE–EPE",
        "role": "MSc programme coordinator",
        "detail": "Admission of non-EU students, tracking MSc EE–EPE progress, evaluation of Extra Project course (ET4399).",
        "href": None,
        "extra": None,
    },
    {
        "kind": "BSc · taught previously",
        "name": "Linear Circuits A & B · EPO-1",
        "code": "EE1C11, EE1C21, EE1L11",
        "role": "Instructor (1 year each)",
        "detail": "Undergraduate circuit and project courses at TU Delft.",
        "href": None,
        "extra": None,
    },
]

INVITED = [
    {"year": "2025", "title": "KU Leuven invited talk", "detail": "Control of HVDC/AC power systems."},
    {"year": "2024", "title": "IEEE ISGT 2024 tutorial (organizer)", "detail": "Control of HVDC/AC electrical grids: RTDS hardware-in-the-loop approach."},
    {"year": "2024", "title": "IEEE ISGT 2024 special session", "detail": "Digitalization in Power Systems — Control of HVDC Power Electronics."},
    {"year": "2024", "title": "ADOreD summer school", "detail": "Design of HVDC advanced control strategies in real time."},
    {"year": "2024", "title": "IET ACDC 2024", "detail": "HVDC control and protection research at TU Delft (with Marjan Popov)."},
    {"year": "2023", "title": "IEEE PowerTech 2023 plenary", "detail": "Enabling interoperability of multi-vendor HVDC grids."},
    {"year": "2023", "title": "DynPOWER / DISC / IEEE PES Serbia & Montenegro", "detail": "Harmonic stability, PE control for renewables, and MMC interoperability lectures."},
    {"year": "2022", "title": "IEEE eGrid & ICAE WiAE panel", "detail": "Control interoperability in MMC-based systems; power-systems research during COVID-19."},
]

EDITORIAL = [
    {"year": "2026–", "title": "Associate Editor, IEEE Transactions on Power Delivery", "detail": "Q1 journal."},
    {"year": "2022–", "title": "Associate Editor, IJEPES (Elsevier)", "detail": "International Journal of Electrical Power & Energy Systems (Q1)."},
    {"year": "2024", "title": "Associate Editor, IET Power Electronics", "detail": "IET."},
    {"year": "2023–2024", "title": "Associate Editor, Electrical Engineering (Springer)", "detail": "Q3 journal."},
    {"year": "2022–2023", "title": "Guest editor roles", "detail": "IEEE Journal of Photovoltaics; IJEPES digital-twin special issue; Renewable & Sustainable Energy Reviews (100% inverter microgrids); MDPI Energies (converter control in low-inertia systems)."},
]

MILESTONES = [
    {"year": "2025", "title": "Associate Professor, TU Delft", "detail": "IEPG / ESE / EEMCS (from May 2025)."},
    {"year": "2025", "title": "MITIGATE-HARM coordinator", "detail": "CETP/NWO European consortium (6 partners, 4 countries)."},
    {"year": "2025", "title": "IEEE Senior Member", "detail": "CAS, PES, IAS, IES, WIE IES; CIGRE B4 JWGs; CRESYM General Assembly."},
    {"year": "2024–", "title": "MSc coordinator, EE–EPE", "detail": "Electrical Power Engineering master’s programme."},
    {"year": "2022", "title": "Tenured Assistant Professor", "detail": "TU Delft tenure track completed."},
    {"year": "2021", "title": "University Teaching Qualification (UTQ)", "detail": "Obtained 22 December 2021."},
    {"year": "2020", "title": "Joined TU Delft", "detail": "Assistant Professor; founded Control of HVDC/AC power systems team."},
    {"year": "2019", "title": "Postdoc, KU Leuven / EnergyVille", "detail": "Harmonic stability multiport modelling in Julia."},
    {"year": "2017", "title": "PhD, University of Belgrade", "detail": "Stable switching control of DC–DC converters."},
]


def clean_pubs():
    pubs = json.loads((EXTRACT / "publications.json").read_text(encoding="utf-8"))
    for p in pubs:
        if not p.get("title"):
            raw = p.get("raw") or ""
            ym = re.search(r"\((\d{4})[a-z]?\)\.\s*(.+)", raw)
            if ym:
                rest = ym.group(2)
                cut = re.split(
                    r"\.\s+(?:doi:|IEEE |International |Electric |Energies|Energy Reports|High Voltage|Heliyon|Tehnika|Journal |e\+i|CIGRE|Special |In |IET |Open |Renewable|Guest |Proceedings|SoftwareX)",
                    rest,
                    maxsplit=1,
                )
                p["title"] = cut[0].strip().rstrip(".")
        if p.get("title") and p["title"][0].islower():
            p["title"] = p["title"][0].upper() + p["title"][1:]
        if not p.get("venue") and p.get("doi"):
            m = re.search(r"\.\s+([^.]+?)\.\s*(?:doi:|" + re.escape(str(p["doi"])) + r")", p.get("raw") or "", re.I)
            if m:
                p["venue"] = m.group(1).strip()
        title = p.get("title") or ""
        # Real paper link only when DOI/landing exists — do not invent one
        if p.get("doi") and not p.get("url"):
            d = str(p["doi"])
            p["url"] = d if d.startswith("http") else f"https://doi.org/{d}"
        if not p.get("scholar") and title:
            q = urllib.parse.quote(f'author:"Aleksandra Lekić" "{title[:80]}"')
            p["scholar"] = f"https://scholar.google.com/scholar?q={q}"
        # Keep entries without paper URL; Scholar button still available

    # Keep essentially everything with a title + year in a sensible window (0 = undated)
    pubs = [
        p
        for p in pubs
        if (p.get("title") or p.get("raw"))
        and p.get("year") is not None
        and (p["year"] == 0 or 2008 <= int(p["year"]) <= 2035)
    ]
    # Only drop clear project deliverables (those live in extras)
    drop_re = re.compile(
        r"Detailed Project Management Plan|\bD\d+\.\d+\b|SUNRISE D\d|InterOPERA D\d|PROSECCO D\d|EASY-RES D\d",
        re.I,
    )
    pubs = [p for p in pubs if not drop_re.search((p.get("title") or "").strip())]

    # Prefer DOI + longer titles; drop truncated CV stubs that are prefixes of fuller entries
    pubs_sorted = sorted(
        pubs,
        key=lambda x: (
            -(x.get("year") or 0),
            0 if x.get("doi") else 1,
            -len(x.get("title") or ""),
            x.get("n") or 0,
        ),
    )
    seen_doi = set()
    kept = []
    for p in pubs_sorted:
        title = (p.get("title") or "").strip().lower()
        doi_k = (p.get("doi") or "").lower().replace("https://doi.org/", "")
        if doi_k and doi_k in seen_doi:
            continue
        if any(title and kt.startswith(title) and len(kt) > len(title) + 8 for kt, _ in kept):
            continue
        if doi_k:
            seen_doi.add(doi_k)
        kept.append((title, p))
    uniq = [p for _, p in kept]
    uniq.sort(key=lambda x: (-x["year"], x.get("n") or 0))
    (EXTRACT / "publications.clean.json").write_text(json.dumps(uniq, indent=2), encoding="utf-8")
    return uniq


def load_pub_extras():
    path = EXTRACT / "publications_extra.json"
    if not path.exists():
        return {"deliverables": [], "books": [], "software": []}
    return json.loads(path.read_text(encoding="utf-8"))


def person_by_slug(slug):
    for t in TEAM:
        if t["slug"] == slug:
            return t
    return None


def project_by_slug(slug):
    for p in PROJECTS:
        if p["slug"] == slug:
            return p
    return None


def card_img(page, src, alt="", logo=True):
    klass = "card-media logo-card" if logo else "card-media"
    return f'<div class="{klass}"><img src="{rel(page, "assets/" + src)}" alt="{escape(alt)}" /></div>'


def build():
    pubs = clean_pubs()

    # Avatars
    for t in TEAM:
        initials = "".join(w[0] for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúčćžšđČĆŽŠĐ]+", t["name"])[:2]).upper()
        if len(initials) < 2:
            initials = t["name"][:2].upper()
        make_avatar(t["slug"], initials)
    # Keep scholar photo if present
    scholar = TEAM_ASSETS / "aleksandra-lekic.jpg"
    # regenerate others only

    for i, item in enumerate(PORTFOLIO):
        make_portfolio_image(item["slug"], item["name"], item.get("image_tone", i))

    # ----- HOME -----
    page = ROOT / "index.html"
    project_cards = []
    for p in PROJECTS:
        if p["status"] != "Current":
            continue
        img = p.get("image") or "offshore-map.jpg"
        project_cards.append(f'''
        <a class="card" href="{rel(page, f"projects/{p['slug']}.html")}">
          {card_img(page, img, p["name"])}
          <div class="card-body">
            <div class="tag">{escape(p["status"])} · {escape(p["years"])}</div>
            <h3>{escape(p["name"])}</h3>
            <p>{escape(p["summary"][:140])}…</p>
            <span class="more">Project page →</span>
          </div>
        </a>''')

    team_cards = []
    for t in TEAM:
        if t.get("status", "current") != "current":
            continue
        if t["type"] == "pi":
            continue
        team_cards.append(f'''
        <a class="card person-card" href="{rel(page, f"team/{t['slug']}.html")}">
          <div class="card-media"><img src="{rel(page, f"assets/team/{t['slug']}.jpg")}" alt="{escape(t["name"])}" /></div>
          <div class="card-body">
            <h3>{escape(t["name"].replace("Dr. Dipl.-Ing. ", "").replace("Dr. ", ""))}</h3>
            <p>{escape(t["role"])} · {escape(t["project"])}</p>
            <span class="more">Profile →</span>
          </div>
        </a>''')
    # include PI first visually: rebuild with PI + others
    pi = next(t for t in TEAM if t["type"] == "pi")
    team_cards.insert(0, f'''
        <a class="card person-card" href="{rel(page, f"team/{pi['slug']}.html")}">
          <div class="card-media"><img src="{rel(page, f"assets/team/{pi['slug']}.jpg")}" alt="{escape(pi["name"])}" /></div>
          <div class="card-body">
            <h3>{escape(pi["name"].replace("Dr. Dipl.-Ing. ", "").replace("Dr. ", ""))}</h3>
            <p>{escape(pi["role"])} · {escape(pi["project"])}</p>
            <span class="more">Profile →</span>
          </div>
        </a>''')
    team_cards = team_cards[:8]

    news_items = []
    for n in NEWS[:4]:
        link = (
            f' <a href="{escape(n["href"])}" target="_blank" rel="noopener">Read more ↗</a>'
            if n.get("href")
            else ""
        )
        news_items.append(f'''
        <article class="list-item">
          <time>{escape(n["date"])}</time>
          <div>
            <h3>{escape(n["title"])}</h3>
            <p class="muted">{escape(n["body"])}{link}</p>
          </div>
        </article>''')

    port_preview = []
    for item in PORTFOLIO[:6]:
        port_preview.append(f'''
        <a class="card" href="{rel(page, f"portfolio/{item['slug']}.html")}">
          <div class="card-media"><img src="{rel(page, f"assets/portfolio/{item['slug']}.jpg")}" alt="{escape(item["name"])}" /></div>
          <div class="card-body">
            <div class="tag">{escape(item["kind"])}</div>
            <h3>{escape(item["name"])}</h3>
            <p>{escape(item["trl"])}</p>
            <span class="more">Details →</span>
          </div>
        </a>''')

    hero_img = rel(page, "assets/hero-hierarchical.jpg")
    body = f'''
  <section class="hero" style="--hero-image: url('{hero_img}')">
    <div class="wrap hero-inner">
      <p class="eyebrow">TU Delft · IEPG · ESE</p>
      <h1>Control of HVDC/AC Power Systems</h1>
      <p class="lede">Interoperable multi-vendor HVDC grids, converter control &amp; protection, and open tools for hybrid AC/DC systems.</p>
      <div class="cta-row">
        <a class="btn btn-primary" href="{rel(page, "projects/index.html")}">Explore projects</a>
        <a class="btn btn-ghost" href="{rel(page, "portfolio/index.html")}">Open-source portfolio</a>
      </div>
    </div>
  </section>

  <section class="block">
    <div class="wrap">
      <p class="sec-label">Research focus</p>
      <h2>Interoperable control &amp; protection for PE-dominated grids</h2>
      <p class="lede-body">Led by Assoc. Prof. Aleksandra Lekić. Circuit theory, nonlinear control, harmonic stability, and real-time validation for multi-terminal HVDC systems — with a growing open-source portfolio on GitHub.</p>
      <div class="cta-row">
        <a class="btn btn-dark" href="{rel(page, "team/aleksandra-lekic.html")}">Meet the PI</a>
        <a class="btn btn-outline" href="{rel(page, "publications/index.html")}">Publications</a>
        <a class="btn btn-outline" href="{rel(page, "awards.html")}">Awards &amp; milestones</a>
      </div>
    </div>
  </section>

  <section class="block strip-dark">
    <div class="wrap">
      <p class="sec-label">Projects</p>
      <h2>Current programmes</h2>
      <p class="lede-body">Each project has its own page with consortium links and team members.</p>
      <div class="grid-3">{"".join(project_cards)}</div>
      <p style="margin-top:1.5rem"><a class="btn btn-ghost" href="{rel(page, "projects/index.html")}">All projects including completed →</a></p>
    </div>
  </section>

  <section class="block">
    <div class="wrap">
      <p class="sec-label">Team</p>
      <h2>Researchers</h2>
      <p class="lede-body">Current researchers — see the team page for alumni and graduated MSc students.</p>
      <div class="grid-4">{"".join(team_cards)}</div>
      <p style="margin-top:1.25rem"><a class="btn btn-outline" href="{rel(page, "team/index.html")}">Full team →</a></p>
    </div>
  </section>

  <section class="block" style="background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line)">
    <div class="wrap">
      <p class="sec-label">News</p>
      <h2>What is happening</h2>
      {"".join(news_items)}
      <p style="margin-top:1.25rem"><a class="btn btn-outline" href="{rel(page, "news/index.html")}">News archive →</a></p>
    </div>
  </section>

  <section class="block">
    <div class="wrap">
      <p class="sec-label">Open source &amp; portfolio</p>
      <h2>Tools from the Interoperability Program</h2>
      <p class="lede-body">Software libraries on GitHub plus hardware products (PACS, DCGC, DCSS) from the Interoperability Program.</p>
      <div class="grid-3">{"".join(port_preview)}</div>
      <p style="margin-top:1.25rem"><a class="btn btn-dark" href="{rel(page, "portfolio/index.html")}">Full portfolio →</a>
      <a class="btn btn-outline" href="https://github.com/control-protection-grids-tudelft" target="_blank" rel="noopener">GitHub org ↗</a></p>
    </div>
  </section>
'''
    write(page, "Home", "index.html", body)

    # ----- TEAM INDEX -----
    page = ROOT / "team" / "index.html"

    def person_cards(members):
        out = []
        for t in members:
            tag = t.get("years") or t["type"]
            out.append(f'''
        <a class="card person-card" href="{rel(page, f"team/{t['slug']}.html")}">
          <div class="card-media"><img src="{rel(page, f"assets/team/{t['slug']}.jpg")}" alt="{escape(t["name"])}" /></div>
          <div class="card-body">
            <div class="tag">{escape(tag)}</div>
            <h3>{escape(t["name"])}</h3>
            <p>{escape(t["role"])}<br />{escape(t["project"])}</p>
            <span class="more">Profile →</span>
          </div>
        </a>''')
        return "".join(out)

    current = [t for t in TEAM if t.get("status", "current") == "current"]
    legacy = [t for t in TEAM if t.get("status") == "legacy"]
    msc_rows = []
    for m in MSC_ALUMNI:
        note = f' · {escape(m["note"])}' if m.get("note") else ""
        msc_rows.append(f'''
        <article class="list-item">
          <div class="meta">{escape(m["year"])}</div>
          <div>
            <h3>{escape(m["name"])}{note}</h3>
            <p class="muted">{escape(m["title"])}</p>
          </div>
        </article>''')

    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Team</p>
    <h1>People</h1>
    <p class="lede">Current researchers and alumni of the Control of HVDC/AC Power Systems group — from Aleksandra Lekić’s CV supervision record.</p>
  </div></section>
  <section class="block"><div class="wrap">
    <h2>Current members</h2>
    <div class="grid-3" style="margin-top:1rem">{person_cards(current)}</div>
  </div></section>
  <section class="block" style="background:#fff;border-top:1px solid var(--line)"><div class="wrap">
    <p class="sec-label">Alumni</p>
    <h2>Legacy team members</h2>
    <p class="lede-body">Former postdocs and PhD graduates supervised in the group.</p>
    <div class="grid-3">{person_cards(legacy)}</div>
  </div></section>
  <section class="block" style="border-top:1px solid var(--line)"><div class="wrap">
    <p class="sec-label">MSc theses</p>
    <h2>Graduated MSc students</h2>
    <p class="lede-body">Selected from the CV supervision list.</p>
    {"".join(msc_rows)}
  </div></section>
'''
    write(page, "Team", "team/index.html", body)

    # ----- TEAM DETAIL -----
    for t in TEAM:
        page = ROOT / "team" / f"{t['slug']}.html"
        links = []
        for label, href in t.get("links", []):
            if href.startswith("http"):
                links.append(f'<a class="btn btn-outline" href="{escape(href)}" target="_blank" rel="noopener">{escape(label)} ↗</a>')
            else:
                links.append(f'<a class="btn btn-outline" href="{rel(page, href)}">{escape(label)}</a>')
        keys = "".join(f"<li>{escape(k)}</li>" for k in t.get("keywords", []))
        email = f'<dt>Email</dt><dd><a href="mailto:{t["email"]}">{t["email"]}</a></dd>' if t.get("email") else ""
        years = f'<dt>Period</dt><dd>{escape(t["years"])}</dd>' if t.get("years") else ""
        status_label = {"legacy": "Alumni", "collaborator": "Collaborator"}.get(t.get("status"), "Current")
        body = f'''
  <section class="page-hero"><div class="wrap">
    <div class="breadcrumbs"><a href="{rel(page, "team/index.html")}">Team</a> / {escape(t["name"])}</div>
    <p class="sec-label">{escape(status_label)} · {escape(t["role"])}</p>
    <h1>{escape(t["name"])}</h1>
    <p class="lede">Project: {escape(t["project"])}{(" · " + escape(t["years"])) if t.get("years") else ""}</p>
  </div></section>
  <section class="block"><div class="wrap detail-grid">
    <aside>
      <div class="portrait"><img src="{rel(page, f"assets/team/{t['slug']}.jpg")}" alt="{escape(t["name"])}" /></div>
      <dl class="side-meta">
        <dt>Role</dt><dd>{escape(t["role"])}</dd>
        <dt>Project</dt><dd>{escape(t["project"])}</dd>
        {years}
        {email}
      </dl>
    </aside>
    <div class="prose">
      <p>{escape(t["bio"])}</p>
      <h2>Keywords</h2>
      <ul>{keys}</ul>
      <div class="link-row">{"".join(links)}
        <a class="btn btn-dark" href="{rel(page, "team/index.html")}">All team</a>
        <a class="btn btn-outline" href="{rel(page, "projects/index.html")}">Projects</a>
      </div>
    </div>
  </div></section>
'''
        write(page, t["name"], "team/index.html", body)

    # ----- PROJECTS INDEX -----
    page = ROOT / "projects" / "index.html"
    def proj_cards(status):
        out = []
        for p in PROJECTS:
            if p["status"] != status:
                continue
            img = p.get("image") or "offshore-map.jpg"
            out.append(f'''
            <a class="card" href="{rel(page, f"projects/{p['slug']}.html")}">
              {card_img(page, img, p["name"])}
              <div class="card-body">
                <div class="tag">{escape(p["years"])} · {escape(p["funder"][:40])}</div>
                <h3>{escape(p["name"])}</h3>
                <p>{escape(p["summary"][:160])}…</p>
                <span class="more">Open project →</span>
              </div>
            </a>''')
        return "".join(out)

    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Projects</p>
    <h1>Research programmes</h1>
    <p class="lede">Current and completed projects with links to official consortium websites.</p>
  </div></section>
  <section class="block"><div class="wrap">
    <h2>Current</h2>
    <div class="grid-3" style="margin:1rem 0 2.5rem">{proj_cards("Current")}</div>
    <h2>Completed</h2>
    <div class="grid-3" style="margin-top:1rem">{proj_cards("Completed")}</div>
  </div></section>
'''
    write(page, "Projects", "projects/index.html", body)

    # ----- PROJECT DETAIL -----
    def prose_paragraphs(text):
        if not text:
            return ""
        return "".join(f"<p>{escape(part.strip())}</p>" for part in text.split("\n\n") if part.strip())

    def bullet_list(items):
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"

    for p in PROJECTS:
        page = ROOT / "projects" / f"{p['slug']}.html"
        people = []
        for slug in p.get("people", []):
            person = person_by_slug(slug)
            if not person:
                continue
            people.append(
                f'<a class="card person-card" href="{rel(page, f"team/{slug}.html")}">'
                f'<div class="card-media"><img src="{rel(page, f"assets/team/{slug}.jpg")}" alt="" /></div>'
                f'<div class="card-body"><h3>{escape(person["name"].split(",")[0])}</h3>'
                f'<p>{escape(person["role"])}</p></div></a>'
            )
        link_btns = []
        if p.get("official"):
            link_btns.append(f'<a class="btn btn-primary" href="{escape(p["official"])}" target="_blank" rel="noopener">Official website ↗</a>')
        if p.get("tud"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(p["tud"])}" target="_blank" rel="noopener">TU Delft page ↗</a>')
        if p.get("github"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(p["github"])}" target="_blank" rel="noopener">GitHub ↗</a>')
        if p.get("docs"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(p["docs"])}" target="_blank" rel="noopener">Documentation ↗</a>')
        if p.get("cordis"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(p["cordis"])}" target="_blank" rel="noopener">CORDIS ↗</a>')
        if p.get("nwo"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(p["nwo"])}" target="_blank" rel="noopener">NWO ↗</a>')
        if p.get("alt"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(p["alt"])}" target="_blank" rel="noopener">Partner site ↗</a>')

        port_by_slug = {item["slug"]: item for item in PORTFOLIO}
        related = []
        for slug in p.get("related_portfolio", []):
            label = port_by_slug.get(slug, {}).get("name") or slug.replace("-", " ").title()
            related.append(f'<li><a href="{rel(page, f"portfolio/{slug}.html")}">{escape(label)}</a></li>')
        related_html = f"<h2>Related portfolio</h2><ul>{''.join(related)}</ul>" if related else ""

        full = p.get("full_name") or p["name"]
        img = p.get("logo") or p.get("image") or "projects/interopera-card.jpg"
        body = f'''
  <section class="page-hero"><div class="wrap">
    <div class="breadcrumbs"><a href="{rel(page, "projects/index.html")}">Projects</a> / {escape(p["name"])}</div>
    <p class="sec-label">{escape(p["status"])} · {escape(p["years"])}</p>
    <h1>{escape(p["name"])}</h1>
    <p class="lede">{escape(full)}</p>
  </div></section>
  <section class="block"><div class="wrap detail-grid">
    <aside>
      <div class="portrait logo-card">
        <img src="{rel(page, "assets/" + img)}" alt="{escape(p["name"])} logo" />
      </div>
      <dl class="side-meta">
        <dt>Role at TU Delft</dt><dd>{escape(p["role"])}</dd>
        <dt>Funder</dt><dd>{escape(p["funder"])}</dd>
        <dt>Period</dt><dd>{escape(p["years"])}</dd>
      </dl>
      <div class="link-row" style="margin-top:1rem;flex-direction:column;align-items:stretch">{"".join(link_btns)}</div>
    </aside>
    <div class="prose">
      <h2>Overview</h2>
      {prose_paragraphs(p.get("overview") or p.get("summary") or "")}
      <h2>Project description</h2>
      {prose_paragraphs(p.get("description") or "")}
      <h2>Objectives &amp; deliverables</h2>
      {bullet_list(p.get("objectives") or [])}
      <h2>Partners</h2>
      <p>{escape(p.get("partners") or "")}</p>
      <h2>TU Delft role</h2>
      <p>{escape(p.get("tud_role") or "")}</p>
      {related_html}
      <h2>Team on this project</h2>
      <div class="grid-3" style="margin-top:1rem">{"".join(people) or "<p class='muted'>See group page.</p>"}</div>
      <div class="link-row" style="margin-top:1.5rem">
        <a class="btn btn-dark" href="{rel(page, "projects/index.html")}">All projects</a>
        <a class="btn btn-outline" href="{rel(page, "portfolio/index.html")}">Portfolio</a>
        <a class="btn btn-outline" href="{rel(page, "news/index.html")}">News</a>
      </div>
    </div>
  </div></section>
'''
        write(page, p["name"], "projects/index.html", body)

    # ----- PORTFOLIO -----
    page = ROOT / "portfolio" / "index.html"

    def port_section(title, items):
        if not items:
            return ""
        cards = []
        for item in items:
            gh = " · GitHub" if item.get("github") else ""
            cards.append(f'''
        <a class="card" href="{rel(page, f"portfolio/{item['slug']}.html")}">
          <div class="card-media"><img src="{rel(page, f"assets/portfolio/{item['slug']}.jpg")}" alt="{escape(item["name"])}" /></div>
          <div class="card-body">
            <div class="tag">{escape(item["kind"])}{gh}</div>
            <h3>{escape(item["name"])}</h3>
            <p>{escape(item["summary"][:140])}…</p>
            <span class="more">{escape(item["trl"])} →</span>
          </div>
        </a>''')
        return f'<h2 style="margin:2rem 0 1rem">{escape(title)}</h2><div class="grid-3">{"".join(cards)}</div>'

    soft = [i for i in PORTFOLIO if i.get("category") == "Software"]
    train = [i for i in PORTFOLIO if i.get("category") == "Training"]
    hard = [i for i in PORTFOLIO if i.get("category") == "Hardware"]
    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Open source &amp; portfolio</p>
    <h1>Interoperability Program portfolio</h1>
    <p class="lede">Software, RTDS libraries, training and hardware from the Interoperability Program — with maturity notes and GitHub links.</p>
  </div></section>
  <section class="block"><div class="wrap">
    <p class="lede-body">Organisation repositories: <a href="https://github.com/control-protection-grids-tudelft" target="_blank" rel="noopener">control-protection-grids-tudelft</a> · <a href="https://github.com/CRESYM" target="_blank" rel="noopener">CRESYM</a>.</p>
    {port_section("Software solutions", soft)}
    {port_section("Training & courses", train)}
    {port_section("Hardware products", hard)}
  </div></section>
'''
    write(page, "Portfolio", "portfolio/index.html", body)

    for item in PORTFOLIO:
        page = ROOT / "portfolio" / f"{item['slug']}.html"
        link_btns = []
        if item.get("github"):
            link_btns.append(f'<a class="btn btn-primary" href="{escape(item["github"])}" target="_blank" rel="noopener">View on GitHub ↗</a>')
        else:
            link_btns.append('<span class="btn btn-ghost" style="cursor:default">Open-source release not yet public</span>')
        if item.get("docs"):
            link_btns.append(f'<a class="btn btn-outline" href="{escape(item["docs"])}" target="_blank" rel="noopener">Documentation ↗</a>')
        related = []
        for slug in item.get("related", []):
            pr = project_by_slug(slug)
            if pr:
                related.append(f'<li><a href="{rel(page, f"projects/{slug}.html")}">{escape(pr["name"])}</a></li>')
        related_html = f"<h2>Related projects</h2><ul>{''.join(related)}</ul>" if related else ""
        plans = item.get("status_plans") or []
        plans_html = "<ul>" + "".join(f"<li>{escape(x)}</li>" for x in plans) + "</ul>" if plans else ""
        desc = item.get("description") or item.get("summary") or ""
        body = f'''
  <section class="page-hero"><div class="wrap">
    <div class="breadcrumbs"><a href="{rel(page, "portfolio/index.html")}">Portfolio</a> / {escape(item["name"])}</div>
    <p class="sec-label">{escape(item["kind"])} · {escape(item["trl"])}</p>
    <h1>{escape(item["name"])}</h1>
    <p class="lede">{escape(item["summary"])}</p>
  </div></section>
  <section class="block"><div class="wrap detail-grid">
    <aside>
      <div class="portfolio-hero-img" style="margin:0"><img src="{rel(page, f"assets/portfolio/{item['slug']}.jpg")}" alt="{escape(item["name"])}" /></div>
      <dl class="side-meta">
        <dt>Category</dt><dd>{escape(item.get("category") or item["kind"])}</dd>
        <dt>Maturity</dt><dd>{escape(item["trl"])}</dd>
      </dl>
      <div class="link-row" style="margin-top:1rem;flex-direction:column;align-items:stretch">{"".join(link_btns)}
        <a class="btn btn-outline" href="{rel(page, "portfolio/index.html")}">All portfolio items</a>
        <a class="btn btn-outline" href="https://github.com/control-protection-grids-tudelft" target="_blank" rel="noopener">Org on GitHub ↗</a>
      </div>
    </aside>
    <div class="prose">
      <h2>Description</h2>
      {prose_paragraphs(desc)}
      <h2>Status &amp; upgrade plans</h2>
      {plans_html or "<p class='muted'>See related projects for context.</p>"}
      {related_html}
    </div>
  </div></section>
'''
        write(page, item["name"], "portfolio/index.html", body)

    # ----- PUBLICATIONS -----
    page = ROOT / "publications" / "index.html"
    extras = load_pub_extras()
    by_year = defaultdict(list)
    for p in pubs:
        by_year[p["year"]].append(p)
    blocks = []
    for year in sorted(by_year.keys(), reverse=True):
        items = []
        year_label = "Undated" if year == 0 else str(year)
        for p in by_year[year]:
            title = p.get("title") or p["raw"][:120]
            authors = p.get("authors") or ""
            kind = p.get("kind") or ""
            tag = f'<span class="tag">{escape(kind)}</span> ' if kind else ""
            href = None
            if p.get("doi"):
                d = str(p["doi"])
                href = d if d.startswith("http") else f"https://doi.org/{d}"
            elif p.get("url") and "scholar.google.com/scholar?q=" not in str(p.get("url")):
                href = p["url"]
            title_html = (
                f'<a href="{escape(href)}" target="_blank" rel="noopener">{escape(title)}</a>'
                if href
                else escape(title)
            )
            links = []
            if href and p.get("doi"):
                links.append(f'<a class="doi" href="{escape(href)}" target="_blank" rel="noopener">doi</a>')
            elif href:
                links.append(f'<a class="doi" href="{escape(href)}" target="_blank" rel="noopener">link</a>')
            scholar = p.get("scholar") or "https://scholar.google.com/citations?user=xwCWAb0AAAAJ&hl=en"
            links.append(f'<a class="doi" href="{escape(scholar)}" target="_blank" rel="noopener">Scholar</a>')
            link_html = " · ".join(links)
            venue = f'<div class="venue">{escape(p.get("venue") or "")}</div>' if p.get("venue") else ""
            items.append(f'''
            <article class="pub-item">
              <div class="authors">{tag}{escape(authors)}</div>
              <h3>{title_html} <span class="pub-links">{link_html}</span></h3>
              {venue}
            </article>''')
        blocks.append(f'<h2 class="year-heading">{escape(year_label)}</h2>' + "".join(items))

    def extra_block(title, items):
        if not items:
            return ""
        rows = []
        for it in items:
            t = it.get("title") or (it.get("raw") or "")[:160]
            meta = " · ".join(x for x in [str(it.get("year") or ""), it.get("authors") or ""] if x)
            href = None
            if it.get("doi"):
                href = it["doi"] if str(it["doi"]).startswith("http") else f"https://doi.org/{it['doi']}"
            elif it.get("url"):
                href = it["url"]
            title_html = (
                f'<a href="{escape(href)}" target="_blank" rel="noopener">{escape(t)}</a>'
                if href
                else escape(t)
            )
            link = f' <a class="doi" href="{escape(href)}" target="_blank" rel="noopener">link</a>' if href else ""
            rows.append(
                f'<article class="pub-item"><div class="authors">{escape(meta)}</div><h3>{title_html}{link}</h3></article>'
            )
        return f'<h2 class="year-heading" style="margin-top:2.5rem">{escape(title)}</h2>' + "".join(rows)

    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Publications</p>
    <h1>Papers by year</h1>
    <p class="lede">{len(pubs)} entries from the CV, ORCID, Semantic Scholar, OpenAlex and Google Scholar. Titles link when a DOI/landing page exists; every entry has a Scholar search link. Profile: <a href="https://scholar.google.com/citations?user=xwCWAb0AAAAJ&hl=en" target="_blank" rel="noopener" style="color:var(--foam)">Google Scholar ↗</a>.</p>
  </div></section>
  <section class="block"><div class="wrap">
    {"".join(blocks)}
    {extra_block("Books & chapters", extras.get("books") or [])}
    {extra_block("Selected software & open-source libraries", extras.get("software") or [])}
    {extra_block("Selected project deliverables", extras.get("deliverables") or [])}
  </div></section>
'''
    write(page, "Publications", "publications/index.html", body)

    # ----- NEWS -----
    page = ROOT / "news" / "index.html"
    by_year = defaultdict(list)
    for n in NEWS:
        by_year[n["year"]].append(n)
    blocks = []
    for year in sorted(by_year.keys(), reverse=True):
        items = []
        for n in by_year[year]:
            link = f' <a href="{escape(n["href"])}" target="_blank" rel="noopener">Read more ↗</a>' if n.get("href") else ""
            items.append(f'''
            <article class="list-item">
              <time>{escape(n["date"])}</time>
              <div><h3>{escape(n["title"])}</h3><p class="muted">{escape(n["body"])}{link}</p></div>
            </article>''')
        blocks.append(f'<h2 class="year-heading">{year}</h2>' + "".join(items))
    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">News &amp; media</p>
    <h1>Newsfeed by year</h1>
    <p class="lede">Group updates and media exposure (IEEE IES newsletters, TU Delft Stories, EEMCS features, and more).</p>
  </div></section>
  <section class="block"><div class="wrap">{"".join(blocks)}</div></section>
'''
    write(page, "News", "news/index.html", body)

    # ----- TEACHING -----
    page = ROOT / "teaching.html"
    course_cards = []
    for c in COURSES:
        links = []
        if c.get("href"):
            links.append(
                f'<a class="btn btn-primary" href="{escape(c["href"])}" target="_blank" rel="noopener">Open course ↗</a>'
            )
        if c.get("extra"):
            links.append(
                f'<a class="btn btn-outline" href="{escape(c["extra"])}" target="_blank" rel="noopener">GitHub models ↗</a>'
            )
        link_row = f'<div class="link-row" style="margin-top:0.75rem">{"".join(links)}</div>' if links else ""
        course_cards.append(f'''
        <article class="list-item" style="display:block">
          <div class="tag">{escape(c["kind"])} · {escape(c["code"])}</div>
          <h3 style="margin:0.4rem 0">{escape(c["name"])}</h3>
          <p class="muted">{escape(c["role"])}</p>
          <p>{escape(c["detail"])}</p>
          {link_row}
        </article>''')
    invited_html = "".join(
        f'<div class="milestone"><div class="y">{escape(i["year"])}</div><div><strong>{escape(i["title"])}</strong><div class="muted">{escape(i["detail"])}</div></div></div>'
        for i in INVITED
    )
    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Teaching</p>
    <h1>Courses &amp; online education</h1>
    <p class="lede">TU Delft MSc teaching, programme coordination, and the IEEE IES MOOC on HVDC/AC control and protection.</p>
  </div></section>
  <section class="block"><div class="wrap">
    <h2>Courses</h2>
    {"".join(course_cards)}
    <h2 style="margin-top:2.5rem">Invited lectures &amp; tutorials</h2>
    {invited_html}
  </div></section>
'''
    write(page, "Teaching", "teaching.html", body)

    # ----- AWARDS -----
    page = ROOT / "awards.html"
    milestones = "".join(
        f'<div class="milestone"><div class="y">{escape(m["year"])}</div><div><strong>{escape(m["title"])}</strong><div class="muted">{escape(m["detail"])}</div></div></div>'
        for m in MILESTONES
    )
    awards_parts = []
    for a in AWARDS:
        link = (
            f' <a href="{escape(a["href"])}" target="_blank" rel="noopener">More ↗</a>'
            if a.get("href")
            else ""
        )
        awards_parts.append(
            f'<div class="milestone"><div class="y">{escape(a["year"])}</div>'
            f'<div><strong>{escape(a["title"])}</strong>'
            f'<div class="muted">{escape(a["detail"])}{link}</div></div></div>'
        )
    awards = "".join(awards_parts)
    editorial = "".join(
        f'<div class="milestone"><div class="y">{escape(e["year"])}</div><div><strong>{escape(e["title"])}</strong><div class="muted">{escape(e["detail"])}</div></div></div>'
        for e in EDITORIAL
    )
    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Recognition</p>
    <h1>Awards, milestones &amp; editorial work</h1>
    <p class="lede">Selected from Aleksandra Lekić’s CV — including PowerWeb best paper (2024), NWO Veni, and editorial appointments.</p>
  </div></section>
  <section class="block"><div class="wrap detail-grid">
    <div>
      <h2>Awards</h2>{awards}
      <h2 style="margin-top:2rem">Editorial work</h2>{editorial}
    </div>
    <div><h2>Milestones</h2>{milestones}</div>
  </div></section>
'''
    write(page, "Awards & milestones", "awards.html", body)

    # ----- CONTACT -----
    page = ROOT / "contact.html"
    body = f'''
  <section class="page-hero"><div class="wrap">
    <p class="sec-label">Contact</p>
    <h1>Get in touch</h1>
    <p class="lede">Control of HVDC/AC Power Systems · IEPG · TU Delft</p>
  </div></section>
  <section class="block"><div class="wrap prose">
    <p><strong>Dr. Dipl.-Ing. Aleksandra Lekić</strong><br />Associate Professor</p>
    <p>Email: <a href="mailto:A.Lekic@tudelft.nl">A.Lekic@tudelft.nl</a><br />
    Phone: +31 15 27 82461<br />
    Office: 36.LB 03.210</p>
    <p>Faculty of Electrical Engineering, Mathematics and Computer Science<br />
    Delft University of Technology</p>
    <div class="link-row">
      <a class="btn btn-primary" href="https://www.tudelft.nl/staff/a.lekic/" target="_blank" rel="noopener">TU Delft staff page ↗</a>
      <a class="btn btn-outline" href="{rel(page, "teaching.html")}">Teaching &amp; MOOC</a>
      <a class="btn btn-outline" href="https://github.com/control-protection-grids-tudelft" target="_blank" rel="noopener">GitHub ↗</a>
      <a class="btn btn-outline" href="https://scholar.google.com/citations?user=xwCWAb0AAAAJ&hl=en" target="_blank" rel="noopener">Google Scholar ↗</a>
    </div>
  </div></section>
'''
    write(page, "Contact", "contact.html", body)

    # GitHub pages config
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print("Done. Publications:", len(pubs))


if __name__ == "__main__":
    build()
