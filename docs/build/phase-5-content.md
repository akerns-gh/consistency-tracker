# Phase 5: Content Management System

## Overview
Implement the content management system with WYSIWYG editor, image upload, HTML sanitization, and content management interface for coaches.

**Estimated Time:** 8-10 hours

## 5.1 WYSIWYG Editor Integration
- Install and configure TinyMCE (recommended) or React Quill
- Set up custom toolbar with required formatting options:
  - Text styles: Bold, Italic, Underline
  - Headings: H1, H2, H3, H4
  - Lists: Bullets, Numbered
  - Alignment: Left, Center, Right
  - Links: Insert/edit hyperlinks
  - Images: Upload or URL
  - Embedded videos: YouTube/Vimeo URLs
  - Tables: Insert/edit tables
  - HTML source view for advanced editing
- Configure image upload handler (S3 pre-signed URLs)
- Configure video embed handler (YouTube/Vimeo validation)
- Set up auto-save functionality (optional, saves draft every 30 seconds)
- Character count display

**Files to create:**
- `frontend/src/components/admin/content/ContentEditor.tsx` - WYSIWYG editor component
- `frontend/src/utils/imageUpload.ts` - Image upload to S3 helper

## 5.2 Content Management Tab (Admin)
- Content list view with filtering by category
- Search functionality
- Create new content page
- Edit existing content
- Preview mode (shows exactly how content appears to players)
- Publish/unpublish toggle
- Drag-and-drop reordering (within categories)
- Delete content
- Content categories: Guidance, Workouts, Nutrition, Mental Performance, Resources
- Slug-based URLs for content pages (URL-friendly identifiers)
- Display order management for navigation menu

**Files to create:**
- `frontend/src/components/admin/content/ContentList.tsx` - Content list view
- `frontend/src/components/admin/content/ContentForm.tsx` - Create/edit form
- `frontend/src/components/admin/content/ContentPreview.tsx` - Preview modal
- `frontend/src/components/admin/content/ContentCard.tsx` - Content card item

## 5.3 Image Upload Implementation
- Pre-signed URL request from Lambda
- Direct S3 upload from frontend
- Image optimization (client-side resize if needed)
- Progress indicator
- Error handling

**Key implementation:**
- `frontend/src/utils/imageUpload.ts` - Complete image upload flow
- Integration with TinyMCE image upload handler

## 5.4 HTML Sanitization
- Server-side sanitization in Lambda (using bleach)
- Client-side sanitization in React (using DOMPurify)
- Validation of iframe sources (YouTube/Vimeo only)
- Content Security Policy headers

**Key implementation:**
- `cdk/lambda/shared/html_sanitizer.py` - Server-side sanitization
- `frontend/src/utils/sanitizeHtml.ts` - Client-side sanitization wrapper

