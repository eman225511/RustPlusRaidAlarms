# Makefile for RustPlusLEDv2
# Cross-platform build automation

.PHONY: build clean install dev test release help

# Default target
all: build

# Build the application
build:
	@echo "🚀 Building RustPlusLED..."
	python build.py

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf dist/ build/ release/ *.spec __pycache__/ *.pyc
	@echo "✅ Clean complete!"

# Install dependencies
install:
	@echo "📥 Installing dependencies..."
	pip install -r requirements.txt

# Development setup
dev: install
	@echo "🔧 Setting up development environment..."
	pip install pyinstaller black flake8

# Test the application
test:
	@echo "🧪 Testing application..."
	python -m py_compile main.py
	python -m py_compile led_controllers.py
	@echo "✅ Syntax check passed!"

# Create release package
release: clean build
	@echo "📦 Creating release package..."
	@echo "✅ Release ready in release/ directory"

# Show help
help:
	@echo "Available targets:"
	@echo "  build    - Build the executable"
	@echo "  clean    - Remove build artifacts"
	@echo "  install  - Install dependencies"
	@echo "  dev      - Setup development environment"
	@echo "  test     - Run syntax checks"
	@echo "  release  - Create clean release package"
	@echo "  help     - Show this help"