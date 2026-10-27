# Resume Optimization Pro

English | [简体中文](./README.md)

[![Version](https://img.shields.io/badge/version-1.1-blue.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-orange.svg)](https://claude.ai/code)

> A professional resume optimization skill tailored for Technical Directors, Managers, and Senior Engineers, featuring an 8-dimensional scoring system refined through real-world case studies.

## 🎯 Target Audience

| Role | Optimization Focus |
|------|-------------------|
| Technical Director | Strategic decisions, business value, impact perspective |
| Technical Manager | Team management, project coordination, process optimization |
| Senior Engineer | Technical solutions, architecture design, innovation |
| Job Seekers | Technical professionals needing systematic optimization |

## 🚀 Quick Start

### Installation

```bash
cd ~/.claude/skills
git clone https://github.com/taielab/resume-optimization-pro.git
```

### Usage

Input directly in Claude Code:

```
Help me optimize this resume: /path/to/resume.md

Analyze my resume quality

Generate interview preparation materials
```

## ✨ Key Features

### 8-Dimensional Scoring System

| Dimension | Weight | Assessment Content |
|-----------|--------|-------------------|
| Information Accuracy | 15 pts | Data verifiability, consistency |
| Structure Rationality | 15 pts | Clear hierarchy, focused priorities, appropriate length |
| Professional Expression | 15 pts | Level-appropriate language, precise terminology |
| Framework Application | 10 pts | CAR/STAR/PAR/SOAR principles |
| Quantified Data | 10 pts | Quantified performance, scale, efficiency |
| Differentiated Competitiveness | 15 pts | Clear unique value proposition |
| ATS Friendliness | 10 pts | Keyword coverage, format compliance |
| Detail Completeness | 10 pts | No redundancy, no omissions, no errors |

**Target**: 90+ score for excellent resumes ready for submission

### Iterative Optimization Process

```
Read Resume → 8D Scoring → Identify Issues → Suggest Improvements → Apply Frameworks → Re-score
    ↑                                                                                    ↓
    └───────────────────── Iterate until 90+ score ────────────────────────────────────┘
```

### Achievement Description Frameworks

| Framework | Use Cases |
|-----------|-----------|
| CAR (Challenge-Action-Result) | Product design, technical decisions, innovation projects |
| STAR (Situation-Task-Action-Result) | Project experience, problem-solving, team management |
| PAR (Problem-Action-Result) | Problem-solving, technical breakthroughs, crisis response |
| SOAR (Situation-Obstacle-Action-Result) | Overcoming difficulties, breaking barriers |

### Interview Preparation Generation

After optimizing resume to 90+, automatically generates:

- **4 Scenario Self-Introductions**: Formal interview, business occasion, tech community, internal team
- **40+ Interview Q&A Bank**: Covering 8 major categories including management, technical, product, strategy, HR
- **Complete STAR Method Answers**: Generated from real resume content

## 💡 v1.1 New Features

### Director-Level Language Conversion

Automatically identifies and converts language style:

❌ **Engineer Perspective**:
```
Proficient in React, Vue, Angular and other mainstream frontend frameworks
Skilled in component development, performance optimization, and engineering configuration
```

✅ **Director Perspective**:
```
Led frontend technology architecture and standardized process development, covering
component library/engineering/performance optimization across all scenarios, driving
tool chain integration and automation with technical decision-making capabilities
```

**Conversion Principles**: Emphasize "led/drove/decided" over "proficient/skilled", focus on system building over tool usage

### Personal vs Company Achievement Distinction

❌ **Wrong**: Writing personal blog operations in company work experience

✅ **Correct**: Personal brand in contact info, work experience only company-related achievements

### Smart Honors & Awards Sorting

Based on 6-second scan rule, sort by **Level > Ranking > Time**, highest honor first

### ATS System Optimization

- Exact keyword matching (include both acronyms and full terms)
- Standard section headers, single-column layout
- Avoid tables, images, special formatting

## 📚 Reference Materials

| Document | Content |
|----------|---------|
| [scoring-rubric.md](references/scoring-rubric.md) | Detailed 8-dimensional scoring criteria |
| [frameworks.md](references/frameworks.md) | CAR/STAR/PAR/SOAR framework details |
| [tailoring-strategies.md](references/tailoring-strategies.md) | Resume customization strategies |
| [resume-structure.md](references/resume-structure.md) | Complete resume structure design guide |

## 🔄 Version History

### v1.1 (2026-02-16)

- 🆕 Director-level language auto-conversion
- 🆕 Personal vs company achievement smart distinction
- 🆕 Honors sorting by level
- 🆕 ATS system deep optimization

### v1.0 (2026-02-15)

- 🎯 8-dimensional scoring system
- 🔄 Iterative optimization process
- 📋 4 achievement description frameworks
- 🎤 Automated interview preparation generation

## 🤝 Contributing

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details

## 📮 Contact

- Project Homepage: https://github.com/taielab/resume-optimization-pro
- Issue Tracking: https://github.com/taielab/resume-optimization-pro/issues
- WeChat Official Account: AI安全工坊

<p align="center">
  <img src="https://img.aiseckit.com/2026/02/9cbc637e6fd668a2dd3b8f897fbab344.png" alt="AI安全工坊">
</p>

---

⭐ If this project helps you, please give it a Star!
