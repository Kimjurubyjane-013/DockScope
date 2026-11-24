# Contributing to DockScope

Thank you for your interest in contributing to **DockScope**!

DockScope is an open-source, community-driven platform. We welcome pull requests, bug reports, feature requests, and documentation improvements.

## Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free experience for everyone. Please be respectful and constructive in all communications.

## Development Workflow

1. **Fork & Branch**: Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-enhancement
   ```

2. **Backend Standards**:
   - Python 3.11+
   - Async SQLAlchemy 2.0 with type annotations.
   - Pydantic v2 schemas for all input/output payloads.
   - All endpoints must include test coverage in `backend/tests`.

3. **Frontend Standards**:
   - Vue 3 Composition API with `<script setup lang="ts">`.
   - Strict TypeScript checking (`npm run type-check` must pass without errors).
   - Tailwind CSS using the design token palette in `tailwind.config.js`.
   - Unit tests in `frontend/tests/unit`.

4. **Testing before submission**:
   ```bash
   # Backend
   pytest backend/tests -v

   # Frontend
   npm run type-check --prefix frontend
   npm run test:unit --prefix frontend
   npm run build --prefix frontend
   ```

5. **Submitting Pull Requests**:
   - Write clear, concise commit messages.
   - Reference any relevant issues in your PR description.
