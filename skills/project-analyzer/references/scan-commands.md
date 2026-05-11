# 结构扫描命令模板

按项目语言/框架选择对应命令组。所有命令都是只读的。

---

## 通用扫描

### 目录结构
```bash
find . -type d -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/__pycache__/*' -not -path '*/.next/*' -not -path '*/coverage/*' -not -path '*/vendor/*' | head -80
```

### 清单文件检测
```bash
ls package.json Cargo.toml go.mod pyproject.toml setup.py pom.xml build.gradle composer.json Gemfile 2>/dev/null
```

### 配置文件
```bash
find . -maxdepth 2 -name '*.config.*' -o -name '.eslintrc*' -o -name 'tsconfig*' -o -name '.prettierrc*' -o -name 'jest.config*' -o -name 'vitest.config*' -o -name '.babelrc*' -o -name 'webpack.config*' -o -name 'vite.config*' -o -name 'rollup.config*' -o -name '.github' -o -name 'Dockerfile' -o -name 'docker-compose*' 2>/dev/null | head -30
```

### 入口文件
```bash
ls src/index.* src/main.* src/app.* src/cli.* src/server.* bin/* cmd/*/main.go 2>/dev/null
```

### 文档文件
```bash
ls README* CONTRIBUTING* CHANGELOG* LICENSE* docs/ 2>/dev/null
```

### Git 信息
```bash
git log --oneline -20 && echo "---" && git shortlog -sn --all | head -10 && echo "---" && git tag --sort=-v:refname | head -10
```

---

## Node.js / TypeScript 特有

### 依赖概览
```bash
node -e "const p=require('./package.json'); console.log('name:', p.name, '\nversion:', p.version, '\nmain:', p.main, '\nmodule:', p.module, '\ntypes:', p.types, '\nbin:', JSON.stringify(p.bin), '\nscripts:', Object.keys(p.scripts||{}).join(', '))"
```

### 主要依赖
```bash
node -e "const p=require('./package.json'); const deps=Object.keys(p.dependencies||{}); const devDeps=Object.keys(p.devDependencies||{}); console.log('dependencies:', deps.slice(0,15).join(', ')); console.log('devDependencies:', devDeps.slice(0,15).join(', '))"
```

### Exports 分析
```bash
node -e "const p=require('./package.json'); ['main','module','exports','types','bin','files','peerDependencies','optionalDependencies'].forEach(k => p[k] && console.log(k+':', JSON.stringify(p[k])))"
```

### Monorepo 检测
```bash
ls packages/*/package.json apps/*/package.json 2>/dev/null && node -e "const p=require('./package.json'); console.log('workspaces:', JSON.stringify(p.workspaces))" 2>/dev/null
```

---

## Go 特有

### 模块信息
```bash
head -30 go.mod
```

### 入口文件
```bash
find . -name 'main.go' -not -path '*/vendor/*' | head -10
```

### 包结构
```bash
find . -type d -not -path '*/vendor/*' -not -path '*/.git/*' | head -50
```

### 命令行入口
```bash
ls cmd/*/main.go 2>/dev/null
```

---

## Python 特有

### 依赖信息
```bash
cat requirements.txt pyproject.toml setup.py setup.cfg 2>/dev/null | head -40
```

### 入口点
```bash
grep -r "if __name__" --include="*.py" | head -10
```

### 包结构
```bash
find . -name '__init__.py' -not -path '*/venv/*' -not -path '*/.venv/*' -not -path '*/site-packages/*' | head -30
```

---

## Rust 特有

### Cargo 信息
```bash
head -50 Cargo.toml
```

### 工作空间
```bash
grep -A 20 '\[workspace\]' Cargo.toml 2>/dev/null
```

### 入口文件
```bash
ls src/main.rs src/bin/*.rs src/lib.rs 2>/dev/null
```

---

## Java / Kotlin 特有

### 构建文件
```bash
cat pom.xml build.gradle build.gradle.kts 2>/dev/null | head -60
```

### 源码结构
```bash
find src -type d | head -30
```

### 入口类
```bash
grep -r "public static void main\|@SpringBootApplication\|fun main" src/ --include="*.java" --include="*.kt" | head -10
```
