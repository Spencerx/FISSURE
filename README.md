# FISSURE - The RF Framework 

<img src="/docs/Icons/README/logo.png">

**Frequency Independent SDR-based Signal Understanding and Reverse Engineering**

[![Watch the video](https://img.youtube.com/vi/abc123XYZ/0.jpg)](https://youtu.be/vUJakWBVnwY)

## Introduction

FISSURE is an **open-source RF framework** that supports both **operational deployments** and **research and education**.
- For **operators**, it provides a rapidly deployable toolkit for signal detection, classification, protocol discovery, fuzzing, vulnerability analysis, and real-time integration with TAK.
- For **educators and researchers**, it lowers the barrier to entry for SDR and reverse engineering, offering a shared environment for learning, experimentation, and publishing new methods.

FISSURE streamlines complex SDR workflows by centralizing software, libraries, and reference material into one consistent framework that runs on desktops, laptops, single-board computers, and ruggedized systems, or scales to distributed tactical nodes networked in the field.

<p align="center">
<img src="/docs/Icons/README/rf_re.png" width="400" height="400">
</p>

## Key Capabilities

- Detect, classify, and analyze RF signals
- Collect, replay, and manipulate IQ data
- Discover protocols and craft custom packets
- Execute fuzzing and vulnerability testing
- Automate workflows with AI and ML integration
- Archive signals and build playlists for testing
- Integrate alerts and data into TAK for team awareness

<p align="center">
<img src="/docs/Icons/README/ecosystem.png" style="max-width: 858px; width: 100%; height: auto;">
</p>

## Deployment Options

<p align="center">
<img src="/docs/Icons/README/fissure_deployments.jpg" style="max-width: 858px; width: 100%; height: auto;">
</p>

- Desktop GUI for visualization and prototyping
- Headless nodes for remote sensing and autonomous operations
- Dockerized services for scalable and repeatable installs
- TAK integration for mission relevance and shared situational awareness

<p align="center">
<img src="/docs/Icons/README/system_overview.png" style="max-width: 858px; width: 100%; height: auto;">
</p>

## Dual-Use Relevance

- **Operators:** detect, geolocate, and respond to RF activity in the field
- **Researchers:** test new algorithms, automation, and AI and ML approaches
- **Educators:** teach SDR, RF security, and reverse engineering in the classroom
- **Students and Hobbyists:** explore SDR workflows without steep setup overhead

## Roadmap and Development

FISSURE’s roadmap evolves with customer demand and community feedback.  
For the most up-to-date view, explore the interactive roadmap:  

👉 [View Interactive Roadmap](https://your-plotly-link)  

### Current Priorities

- Expanding support for distributed tactical nodes and remote deployments  
- Improving automation and information sharing between components  
- Enhancing TAK integration and real-time alerting  
- Adding new protocol libraries, analysis tools, and training material  

## White Papers

FISSURE is supported by a series of white papers that explore both technical and operational applications across different domains.

1. [Overview](link_here)
2. [Counter-UAS](link_here)
3. [Drone Payloads & Aerial Ops](link_here)
4. [Maritime & Port Protection](link_here)
5. [Vehicle & Mobility Systems](link_here)
6. [Perimeter & Infrastructure Defense](link_here)
7. [ATAK & Mobile Integration](link_here)
8. [Training & Education](link_here)
9. [Technical Details & Architecture](link_here)

## Blog Posts

AIS has published several articles highlighting FISSURE’s applications, updates, and use cases:
- [Demonstrating FISSURE as a Drone Payload at Northern Strike 2025](https://www.ainfosec.com/fissure-demo-at-northern-strike)
- [A Recap of My DEF CON 2024 Presentation on FISSURE Updates](https://www.ainfosec.com/a-recap-of-my-def-con-2024-presentation-on-fissure-updates)
- [FISSURE: Navigating the Open-Source Realm](https://www.ainfosec.com/fissure-navigating-the-open-source-realm)
- [FISSURE: The RF Framework for Everyone](https://www.ainfosec.com/fissure-the-rf-framework-for-everyone)

[See all AIS blog posts](https://www.ainfosec.com/blog/)

## News

![NEW](https://img.shields.io/badge/NEW-Documentation-brightgreen) 

**Updated Info Sheet** https://www.ainfosec.com/wp-content/uploads/2023/04/AIS-FISSURE.pdf

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Alerts and Sensor Node Positions in WebTAK** View GPS tagged alerts with custom text and sensor node GPS beacons in a WebTAK browser.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Attack Alerts, Reports, Exploit Recommendations** Create custom messages from attacks that show up in the Dashboard. Stage new attacks with the return data from a single button click.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Alert Listeners** for creating backchannels that accept alerts. Includes: folder/file changes, Meshtastic, MQTT, serial, TCP/UDP, website polling, and ZMQ SUB.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**GPS Acquisition and Mapping** in sensor node configuration.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Plugins** to import and export capabilities into the FISSURE library and share with collaborators. (A work in progress)

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Demo Menu** to aid with future automated testing and to provide examples of Dashboard operation to users.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Z-Wave and Ceiling Fans Lessons** to highlight FISSURE as a reverse engineering tool. [Lesson13: Z-Wave](/docs/Lessons/Markdown/Lesson13_Z-Wave.md), [Lesson14: Ceiling Fans](/docs/Lessons/Markdown/Lesson14_Ceiling_Fans.md)

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Recall Installer Setups** Export and import checked software items in the FISSURE installer using the Export and Import buttons. Quickly install only the programs you need.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Local IQEngine Support** in the IQ Data tab and menu for loading in SigMF files with one click for files in the "/IQ Recordings" folder. Stop the IQEngine docker container using the Tools>Data>IQEngine menu.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Deployable remote sensor nodes** for general-purpose computers (SBCs, mini PCs, laptops, desktops) that support any type of peripheral that can be controlled by a computer. These remote sensor nodes run a small subset of code that can be controlled over a network through the FISSURE Dashboard GUI to perform traditional FISSURE operations and also execute new types of scripted actions that can be run autonomously on startup or semi-autonomously through user interaction (autorun playlists). 

The deployment of multiple sensor nodes on the same network unlocks many geospatial applications for future development of FISSURE. Such applications include direction finding, tracking, intrusion detection, mobile deployment, and perimeter defense. A small form factor and autonomous capabilities grant unique opportunities for stealth deployment and packaging onto existing platforms. These updates can also provide a low-cost mechanism for remote workers to conduct combined RF-cybersecurity testing and access specialized RF environments like international localities of interest, laboratories, and test sites.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Trigger capabilities** for autorun playlists, single-stage attacks, multi-stage attacks, and archive replay. Includes over 20 examples of acoustic, environmental, filesystem, networking, RF, time, and visual triggers for kicking off electromagnetic effects. Refer to the [Trigger List](https://fissure.readthedocs.io/en/latest/pages/operation.html#trigger-list) section in the user manual for the current list and the [Creating Triggers](https://fissure.readthedocs.io/en/latest/pages/development.html#creating-triggers) section on how to add your own.

![NEW](https://img.shields.io/badge/NEW-Feature-brightgreen) 

**Signal Classifier tab** for training decision tree and DNN models based solely on extracted statistical features from IQ data. This tab is used to assign truth information to features sets (produced from Feature Extractor) gathered from isolated signals files (produced from Signal Conditioner) to develop machine learning models using TensorFlow and scikit-learn. Unknown signals can be run through all available models to compare results and establish confidence. The Signal Conditioner, Feature Extractor, and Signal Classifier tabs act as a testbed for developing new algorithms and eventually the results (isolated IQ signals, statistical features, classification confidence) will be cataloged into the FISSURE library as signals of interest for further analysis or to trigger automated actions.

### Upcoming/Recent Events

![Conference](https://img.shields.io/badge/Event-Conference-darkgray) **Sat. August 10, 2024**: DEF CON 32 - RF Village - 1400-1500 PST. [Prerecorded Video](https://www.youtube.com/watch?v=5nYiVR-PsOc), [Live Recording](https://www.youtube.com/watch?app=desktop&v=mhbJHOGrCik)

![Career Fair](https://img.shields.io/badge/Event-Career%20Fair-darkgray) **Thu. September 5, 2024**: Binghamton University STEM Job and Internship Fair - 1100-1530 EST

![Conference](https://img.shields.io/badge/Event-Conference-darkgray) **Tue. September 17, 2024**: GNU Radio Conference 2024 - 1605-1635 EST [Description/Slides](https://events.gnuradio.org/event/24/contributions/649/), [Live Recording](https://youtu.be/5UYhUi8SiK4?t=27282)

![CTF](https://img.shields.io/badge/Event-CTF-purple) **January 20, 2025 (Runs Indefinitely)**: FISSURE Challenge. [Link](https://fissure.ainfosec.com/) (Now Live)

![Career Fair](https://img.shields.io/badge/Event-Career%20Fair-darkgray) **Thu. February 6, 2025**: Binghamton University Spring 2025 Job and Internship Fair - 1100-1500 EST

![Exhibition](https://img.shields.io/badge/Event-Exhibition-green) **May 5-8, 2025**: SOF Week - Assured Information Security, Inc. (AIS) booth

## Documentation

<p align='center'>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_user_manual.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_user_manual.png" width=110px, height=110px>
  <img alt="User Manual" src="">
</picture>
</a>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/pages/installation.html">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_installation.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_installation.png" width=110px, height=110px>
  <img alt="Installation" src="">
</picture>
</a>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/pages/hardware.html">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_hardware.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_hardware.png" width=110px, height=110px>
  <img alt="Hardware" src="">
</picture>
</a>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/pages/components.html">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_components.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_components.png" width=110px, height=110px>
  <img alt="Components" src="">
</picture>
</a>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/pages/operation.html">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_operation.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_operation.png" width=110px, height=110px>
  <img alt="Operation" src="">
</picture>
</a>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/pages/development.html">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_development.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_development.png" width=110px, height=110px>
  <img alt="Development" src="">
</picture>
<a target="_blank" href="https://fissure.readthedocs.io/en/latest/pages/about.html">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="/docs/Icons/README/documentation_credits.png" width=110px, height=110px>
  <source media="(prefers-color-scheme: light)" srcset="/docs/Icons/README/documentation_credits.png" width=110px, height=110px>
  <img alt="Credits" src="">
</picture>
</a>
</p>

- [Info Sheet](https://www.ainfosec.com/wp-content/uploads/2023/04/AIS-FISSURE.pdf)
- [AIS Page](https://www.ainfosec.com/technologies/fissure/)
- [GRCon22 Slides](https://events.gnuradio.org/event/18/contributions/246/attachments/84/164/FISSURE_Poore_GRCon22.pdf)
- [GRCon22 Paper](https://events.gnuradio.org/event/18/contributions/246/attachments/84/167/FISSURE_Paper_Poore_GRCon22.pdf)
- [Hack Chat Transcript](https://hackaday.io/event/187076-rf-hacking-hack-chat/log/212136-hack-chat-transcript-part-1)

## Capabilities

- [FISSURE Capabilities (Updated: 11Sep24)](https://docs.google.com/viewer?url=https://raw.githubusercontent.com/ainfosec/FISSURE/Python3/docs/Help/FISSURE_Capabilities.pdf)

<table style="padding:10px">
  <tr>
    <td><img src="/docs/Icons/README/detector.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Signal Detector</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/iq.png" align="center" width="200" height="165"><dt align="center"><small><i><b>IQ Manipulation</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/library.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Signal Lookup</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/pd.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Pattern Recognition</b></i></small></dt></td>
  </tr>
  <tr>
    <td><img src="/docs/Icons/README/attack.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Attacks</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/fuzzing.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Fuzzing</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/signal_playlists.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Signal Playlists</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/gallery.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Image Gallery</b></i></small></dt></td>
  </tr>
  <tr>
    <td><img src="/docs/Icons/README/packet.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Packet Crafting</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/scapy.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Scapy Integration</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/crc_calculator.png" align="center" width="200" height="165"><dt align="center"><small><i><b>CRC Calculator</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/log.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Logging</b></i></small></dt></td>
  </tr>  
  <tr>
    <td><img src="/docs/Icons/README/dataset_builder.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Dataset Builder</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/online_archive.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Online Archive</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/third-party_tools.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Third-Party Tools</b></i></small></dt></td>
    <td><img src="/docs/Icons/README/dark_mode.png" align="center" width="200" height="165"><dt align="center"><small><i><b>Dark and Custom Themes</b></i></small></dt></td>
  </tr>  
</table>

## Videos

- [FISSURE Videos](https://www.youtube.com/playlist?list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_)
- [AIS YouTube](https://www.youtube.com/@assuredinformationsecurity/featured)

<table border="0px">
  <tr>
    <td><a href="https://www.youtube.com/watch?v=PGIZHhLswXg&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_install.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Install</b></i></small></dt></td>
    <td><a href="https://www.youtube.com/watch?v=k6JbpNsTazc&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_tsi.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Target Signal Identification</b></i></small></dt></td>
    <td><a href="https://www.youtube.com/watch?v=aGhWxKWe6pI&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_pd.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Protocol Discovery</b></i></small></dt></td>
  </tr>
  <tr>
    <td><a href="https://www.youtube.com/watch?v=jeH0HtnMK10&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_packet_crafter.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Packet Crafter</b></i></small></dt></td>
    <td><a href="https://www.youtube.com/watch?v=gKrClyGxLXY&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_iq_data.png" align="center" width="250" height="140"><dt align="center"><small><i><b>IQ Data</b></i></small></dt></td>
    <td><a href="https://www.youtube.com/watch?v=I8TU7boIi_U&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_archive.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Archive</b></i></small></dt></td>
  </tr>
  <tr>
    <td><a href="https://www.youtube.com/watch?v=iJuMXupZkPY&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_attack.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Attack</b></i></small></dt></td>
    <td><a href="https://www.youtube.com/watch?v=fK5h9FScwjc&list=PLs4a-ctXntfjpmc_hrvI0ngj4ZOe_5xm_"><img src="/docs/Icons/README/youtube_library.png" align="center" width="250" height="140"><dt align="center"><small><i><b>Library</b></i></small></dt></td>
    <td><a href="https://www.youtube.com/watch?v=1f2umEKhJvE"><img src="/docs/Icons/README/GRCon22_Video.png" align="center" width="250" height="140"><dt align="center"><small><i><b>GRCon22</b></i></small></dt></td>
  </tr>
  <tr>
    <td><a href="https://www.youtube.com/watch?v=5nYiVR-PsOc"><img src="/docs/Icons/README/youtube_dc32_rf_village_prerecorded.png" align="center" width="250" height="140"><dt align="center"><small><i><b>DC32 RF Village Prerecorded Talk</b></i></small></dt></td>
    <td><a href="https://youtu.be/5UYhUi8SiK4?t=27282"><img src="/docs/Icons/README/youtube_GRCon24.png" align="center" width="250" height="140"><dt align="center"><small><i><b>GRCon24</b></i></small></dt></td>
    <td></td>
  </tr>   
</table>

## Hardware

The following is a list of "supported" hardware with varying levels of integration:
- USRP: X3xx, B2xx, B20xmini, USRP2, N2xx, X410
- HackRF
- RTL2832U
- 802.11 Adapters
- LimeSDR
- bladeRF, bladeRF 2.0 micro
- Open Sniffer
- PlutoSDR
- SDRplay: RSPduo, RSPdx, RSPdx R2

## Getting Started

**Supported**

There are now two branches within FISSURE: the Python3 branch and the Python2_maint-3.7 branch. The Python3 branch contains the latest code and has support for PyQt5 and GNU Radio versions 3.8 and 3.10. The Python2_maint-3.7 branch has been deprecated and will only be updated if specific third-party tools require GNU Radio version 3.7 or an older operating system. Only the latest minor versions of operating systems will be supported for installs and we will do our best to keep up.

The GitHub releases provided in this repository are periodic snapshots of the project's state, intended primarily for archival purposes. These releases may not include the latest updates, bug fixes, or features currently under development. To access the most up-to-date version of the software, we strongly recommend using the main Python3 branch, which reflects ongoing development and the current state of the project.

FISSURE is most extensively tested on Ubuntu, making it the most validated platform.

Operating System | FISSURE Branch | Default GNU Radio Version
:-------------------------:|:-------------------------:|:-------------------------:
| BackBox Linux 8 (amd64) | Python3 | maint-3.10 |
| Kali 23.1 (x64) | Python3 | maint-3.10 |
| KDE neon 5.25 (x64) (6.0 not tested) | Python3 | maint-3.8 |
| Parrot Security 6.1 (amd64) | Python3 | maint-3.10 |
| Raspberry Pi OS (bookworm) | Python3 | maint-3.10 |
| Ubuntu 18.04 (x64) | Python2_maint-3.7 | maint-3.7 |
| Ubuntu 20.04 (x64) | Python3 | maint-3.8 |
| Ubuntu 22.04 (x64) | Python3 | maint-3.10 |
| Ubuntu 22.04 (ARM/Orange Pi) | Python3 | maint-3.10 |
| Ubuntu 24.04 (x86) | Python3 | maint-3.10 |
| Windows 11 WSL2 | See Supported Linux Version | See Supported Linux Version |

**In-Progress (beta)**

These operating systems are still in beta status. They are under development and several features are known to be missing. Items in the installer might conflict with existing programs or fail to install until the status is removed.

Operating System | FISSURE Branch | Default GNU Radio Version
:-------------------------:|:-------------------------:|:-------------------------:
| DragonOS Noble (24.04) | Python3 | maint-3.10 |
| Ubuntu for Raspberry Pi | Python3 | maint-3.10 |

Note: Certain software tools do not work for every OS. Refer to [Known Conflicts and Third-Party Software](https://fissure.readthedocs.io/en/latest/pages/installation.html#known-conflicts)

**Installation** 

For adding SSH keys to GitHub and cloning with SSH (needed for contributing):
```
ssh-keygen -t ed25519
cat ~/.ssh/id_ed25519.pub
Paste text into "Settings" > "SSH and GPG keys" > "New SSH Key"
git clone git@github.com:ainfosec/FISSURE.git 
```

For cloning with https:
```
git clone https://github.com/ainfosec/FISSURE.git
```

Preparing the installer:
```
cd FISSURE
git checkout Python3  # Optional, or Python2_maint-3.7 for select legacy third-party tools
./install
```

Notes:
- The installer will ask to install PyQt software dependencies required to launch the installation GUIs if they are not found. 
- Select the operating option in the GUI that best matches your operating system (should be detected automatically if your OS matches an option).
- Periodically answer prompts regarding third-party software throughout the install. Use your best judgment, the answers will not likely impact FISSURE.
- Ensure your system clock is set correctly to avoid errors with apt rejecting repository updates.
- After installation, reboot your computer or log out and back in so that user group changes take effect.

<p align="center">
<img src="/docs/Icons/README/install1.png" width="257" height="379">
</p>

It is recommended to install FISSURE on a clean operating system to avoid conflicts with existing software. Further efforts towards virtualization and dependency management will be continued. Notes on the installer:
- The items listed under the "Minimum Install" category are what is required to launch the FISSURE Dashboard without errors. 
- The radio hardware and out of tree modules are required to perform many actions in FISSURE.
- The flow graphs need to be recompiled to avoid errors across GNU Radio minor versions.
- Software programs outside the minimum install are optional and can be installed as needed. 
- Select all the recommended checkboxes (Default button) to avoid errors while operating the various tools within FISSURE. 
- Items unchecked by default may not install properly or could possibly conflict with existing programs (please suggest fixes!). 
- There will be multiple prompts throughout the installation, mostly asking for elevated permissions and user names. These prompts are primarily tied to third-party tools, refer to installation instructions provided by the maintainer for details.
- If an item contains a "Verify" section at the end, the installer will run the command that follows and highlight the checkbox item green or red depending on if any errors are produced by the command. Checked items without a "Verify" section will remain black following the installation.
- To avoid installation and permission errors, download FISSURE to a user owned directory such as Home. Run the install script and the fissure command without using sudo. Many of the third-party tools will be downloaded to and installed from the `~/Installed_by_FISSURE` directory.

<p align="center">
<img src="/docs/Icons/README/install2.png" width="692" height="479">
</p>

The FISSURE installer is helpful for staging computers or installing select software programs of interest. The code can be quickly modified to allow for custom software installs. The size estimates for the programs are before and after readings from a full install. The sizes for each program are not exact as some dependencies are installed in previously checked items. The sizes may also change over time as programs get updated.

<p align="center">
<img src="/docs/Icons/README/install3.png" width="692" height="479">
</p>

**Remote Sensor Node Installation**

Install FISSURE per usual on a general purpose computer. Install FISSURE on the remote computer in the same directory location as the local computer (until further notice) to avoid filepath errors with certain actions. To configure the sensor node for remote operation, edit the "default.yaml" file in the `./fissure/Sensor_Node/Sensor_Node_Config/` directory. Edit the following fields to change from local to remote operation:
- nickname: (anything but "Local Sensor Node")
- ip_address: (your remote sensor node computer's ip_address)

Change the "autorun" field from from `false` to `true` to run the default autorun playlist file on startup and forgo remote operations. New autorun playlists can be generated and saved from the Dashboard Autorun tab.

The remote sensor node acts as a server and must have a set of valid certificates (generated during install) that match with the client (local computer). The server needs the "server.key_secret" and "client.key" files while the client needs the "client.key_secret" and "server.key" files. If the certificates folder was generated on the server computer, the client files must be manually transferred to the other computer.

**Local Dashboard Usage**

Open a new terminal after installation and enter:

```
fissure
```

The intended method for launching the FISSURE Dashboard is through the terminal without sudo. The terminal provides important status and feedback for some operations. Refer to the FISSURE documentation for more details. 

A local sensor node can be launched through the top buttons in the FISSURE Dashboard and helps maintain all pre-existing FISSURE functionality on a standalone workstation. Only one local and four remote sensor nodes (or five remote) are supported at this time. 

If any of the programs freeze or hang on close, the following commands can be used to detect a problem or forcibly shut down:
```
sudo ps -aux | grep fissure
sudo pkill python3
sudo kill -9 <PID of __main__.py>
```

**Remote Sensor Node Usage**

After configuring the sensor node config file (see above), the sensor node code can be run using this command in a terminal:

```
fissure-sensor-node
```

The sensor node code will stay active until ctrl+c is applied. Connecting to the remote sensor node is performed through the top buttons of the FISSURE Dashboard. Right-clicking the top buttons will select an active sensor node to perform operations. Future operations that utilize more than one node at a time will be handled on a case-by-case basis within the individual tabs.

**Windows 11 WSL2 Instructions**

FISSURE can run in Windows 11 using WSL2 for supported Linux operating systems. The following are instructions to help install WSL2, install a Linux operating system, set up USB passthrough, and install FISSURE in the Linux operating system.

Install WSL2:

1. Open PowerShell as Administrator
2. `wsl --install`
3. Enable Virtualization in BIOS, check using: Task Manager>Performance>CPU>Virtualization
4. `wsl --set-default-version 2`
5. `wsl --list --online`
6. Install a specific version (plain Ubuntu should be the latest version listed): `wsl --install -d Ubuntu-22.04`
7. Open the Start Menu, search for Ubuntu and launch it
8. To uninstall a distribution: `wsl --unregister Ubuntu-22.04`

Enable USB passthrough in a PowerShell as Administrator:

1. `winget install usbipd`
2. Add usbipd to System PATH: Start Menu>Environment Variables>Edit the system environment variables>System Properties>Environment Variables>System Variables>Path>Edit>New: `C:\Program Files\usbipd-win`
3. Close and reopen PowerShell as Administrator
4. `usbipd wsl list`
5. `usbipd wsl attach --busid <BUS_ID>` or `usbipd wsl attach --busid <BUS_ID> --wsl <DistributionName>` (replace <BUS_ID> with the actual BUS ID of the device)
6. To detach: `usbipd wsl detach --busid <BUS_ID>`

Install FISSURE in Linux Terminal:

1. `sudo apt-get install git`
2. Clone FISSURE and install as detailed above

## Lessons

FISSURE comes with several helpful guides to become familiar with different technologies and techniques. Many include steps for using various tools that are integrated into FISSURE. We aim to improve the quality and add new content over time.
- [Lesson1: OpenBTS](/docs/Lessons/Markdown/Lesson1_OpenBTS.md)
- [Lesson2: Lua Dissectors](/docs/Lessons/Markdown/Lesson2_LuaDissectors.md)
- [Lesson3: Sound eXchange](/docs/Lessons/Markdown/Lesson3_Sound_eXchange.md)
- [Lesson4: ESP Boards](/docs/Lessons/Markdown/Lesson4_ESP_Boards.md)
- [Lesson5: Radiosonde Tracking](/docs/Lessons/Markdown/Lesson5_Radiosonde_Tracking.md)
- [Lesson6: RFID](/docs/Lessons/Markdown/Lesson6_RFID.md)
- [Lesson7: Data Types](/docs/Lessons/Markdown/Lesson7_Data_Types.md)
- [Lesson8: Custom GNU Radio Blocks](/docs/Lessons/Markdown/Lesson8_Custom_GNU_Radio_Blocks.md)
- [Lesson9: TPMS](/docs/Lessons/Markdown/Lesson9_TPMS.md)
- [Lesson10: Ham Radio Exams](/docs/Lessons/Markdown/Lesson10_Ham_Radio_Exams.md)
- [Lesson11: Wi-Fi Tools](/docs/Lessons/Markdown/Lesson11_WiFi_Tools.md)
- [Lesson12: Creating Bootable USBs](/docs/Lessons/Markdown/Lesson12_Creating_Bootable_USBs.md)
- [Lesson13: Z-Wave](/docs/Lessons/Markdown/Lesson13_Z-Wave.md)
- [Lesson14: Ceiling Fans](/docs/Lessons/Markdown/Lesson14_Ceiling_Fans.md)

## FISSURE Challenge - Continuous Capture the Flag

<p align="center">
  <a href="https://fissure.ainfosec.com/">
    <img src="/docs/Icons/README/fissure_challenge.jpeg" alt="fissure_challenge" height="150" />
  </a>
</p>

The **FISSURE Challenge** is a continuous capture-the-flag contest built around the FISSURE framework. It is designed as an open learning tool where anyone can practice RF reverse engineering, explore new features, and tackle protocol-focused challenges.  

- New challenges are added over time as FISSURE evolves.  
- Solutions and walkthroughs are posted periodically on YouTube. [Solutions 1](https://www.youtube.com/watch?v=jYtqWwG_-kI)
- Community members are encouraged to **submit their own challenges** for others to solve.

Access the challenges at: [FISSURE Challenge](https://fissure.ainfosec.com/)

## Contributing

Suggestions for improving FISSURE are strongly encouraged. Leave a comment in the [Discussions](https://github.com/ainfosec/FISSURE/discussions) page or in the Discord Server if you have any thoughts regarding the following:
- New feature suggestions and design changes
- Software tools with installation steps
- New lessons or additional material for existing lessons
- RF protocols of interest
- More hardware and SDR types for integration
- IQ analysis scripts in Python
- Installation corrections and improvements

Contributions to improve FISSURE are crucial to expediting its development. Any contributions you make are greatly appreciated. If you wish to contribute through code development, please fork the repo and create a pull request:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

Creating [Issues](https://github.com/ainfosec/FISSURE/issues) to bring attention to bugs is also welcomed.

Need more specific ideas? There are a lot of topics we have yet to investigate. Check out our running list of potential [to-do items](./TODO.md). Any help is appreciated. Pick an easy one and write that you contributed to FISSURE in your resume/CV.

Are you a student or looking to learn more about RF and programming or an organization looking to expose students to the world of open source? Reach out today and refer to the [2023 Project Idea List](./idea_list.md).

## Collaborating

Contact Assured Information Security, Inc. (AIS) Business Development to propose and formalize any FISSURE collaboration opportunities–whether that is through dedicating time towards integrating your software, having the talented people at AIS develop solutions for your technical challenges, or integrating FISSURE into other platforms/applications.  

## License

GPL-3.0

For license details, see LICENSE file.

## Contact

Join the Discord Server: [https://discord.gg/JZDs5sgxcG](https://discord.gg/JZDs5sgxcG)

Follow on Twitter/X: [@FissureRF](https://twitter.com/fissurerf), [@AinfoSec](https://twitter.com/ainfosec)

Follow on Bluesky: [@fissurerf.bsky.social](https://bsky.app/profile/fissurerf.bsky.social)

Connect on LinkedIn: [FISSURE - The RF Framework](https://www.linkedin.com/company/fissure-the-rf-framework)

Chris Poore - Assured Information Security, Inc. - poorec@ainfosec.com

Business Development - Assured Information Security, Inc. - bd@ainfosec.com

## Testimonials

> “FISSURE is a powerful and versatile RF software platform suitable for both education and practical applications.  
> It supports a wide range of commonly used hardware and offers intuitive IQ data analysis tools.  
> These features enable us to visualize, interpret, and directly modify RF signal messages in our project.”  
> – Dylan R.

> “We really enjoyed using FISSURE in our engineering project.  
> This software is an incredibly comprehensive collection of tools to manipulate radio frequencies and was an amazing aid to our studies involving wireless communications.”  
> – University Senior Project Team

## Acknowledgments

Special thanks to Dr. Samuel Mantravadi and Joseph Reith for their contributions to this project.

<img src="/docs/Icons/README/logo1.png">

## Assured Information Security
Like working with signals, reverse engineering, or other realms in cybersecurity? Browse our [current openings](https://recruiting.paylocity.com/recruiting/jobs/All/4cc515ee-a8ad-4e3a-ac7d-c105c5d24074/ASSURED-INFORMATION-SECURITY-INC) or join our [talent community](https://recruiting.paylocity.com/Recruiting/PublicLeads/New/4cc515ee-a8ad-4e3a-ac7d-c105c5d24074) for future consideration. 

If you have an interest in hacking, check out our [Can You Hack It?®](https://www.canyouhackit.com) challenge and test your skills! Submit your score to show us what you’ve got. AIS has a national footprint with offices and remote employees across the U.S. We offer competitive pay and outstanding benefits. Join a team that is not only committed to the future of cyberspace, but to our employee’s success as well.

<p align="center">
  <a href="https://www.ainfosec.com/">
    <img src="/docs/Icons/README/ais.png" alt="ais" height="100" />
  </a>
</p>
