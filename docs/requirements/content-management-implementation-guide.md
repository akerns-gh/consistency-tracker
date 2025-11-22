# Content Management System - Implementation Guide

## Overview
This guide provides detailed implementation instructions for the HTML content management system that allows coaches to create and edit guidance pages, workout plans, nutrition tips, and other resources for players.

## Key Features
1. WYSIWYG HTML editor for coaches (no coding required)
2. Content organized by categories (Guidance, Workouts, Nutrition, etc.)
3. Image upload and management
4. Video embedding (YouTube, Vimeo)
5. Publish/unpublish workflow
6. Mobile-responsive content rendering
7. HTML sanitization for security

## Security Requirements

### HTML Sanitization (CRITICAL)
All HTML content must be sanitized on both server-side (Lambda) and client-side (React) to prevent XSS attacks.

**Python Lambda Sanitization (using bleach library):**
```python
import bleach

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'img', 'iframe', 'table', 'thead', 'tbody',
    'tr', 'td', 'th', 'div', 'span', 'blockquote', 'code', 'pre'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen'],
    'table': ['class'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan'],
    'div': ['class'],
    'span': ['class']
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

ALLOWED_IFRAME_DOMAINS = [
    'www.youtube.com',
    'youtube.com',
    'player.vimeo.com',
    'vimeo.com'
]

def sanitize_html(html_content):
    """Sanitize HTML content to prevent XSS attacks"""
    # First pass: Basic sanitization
    clean_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    # Validate iframe sources
    clean_html = validate_iframe_sources(clean_html)
    
    return clean_html

def validate_iframe_sources(html_content):
    """Ensure iframes only come from approved domains"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if not any(domain in src for domain in ALLOWED_IFRAME_DOMAINS):
            iframe.decompose()  # Remove unauthorized iframe
    
    return str(soup)
```

**React Client-Side Sanitization (using DOMPurify):**
```javascript
import DOMPurify from 'dompurify';

const sanitizeConfig = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'a', 'img', 'iframe', 'table', 'thead', 'tbody',
    'tr', 'td', 'th', 'div', 'span', 'blockquote', 'code', 'pre'
  ],
  ALLOWED_ATTR: [
    'href', 'title', 'target', 'rel', 'src', 'alt', 'width', 'height',
    'frameborder', 'allowfullscreen', 'class', 'colspan', 'rowspan'
  ],
  ALLOW_DATA_ATTR: false
};

function ContentDisplay({ htmlContent }) {
  const sanitizedHTML = DOMPurify.sanitize(htmlContent, sanitizeConfig);
  
  return (
    <div 
      className="content-display"
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
    />
  );
}
```

## Image Upload Implementation

### Pre-Signed URL Generation (Lambda)
```python
import boto3
import uuid
from datetime import datetime, timedelta

s3_client = boto3.client('s3')
CONTENT_IMAGES_BUCKET = os.environ['CONTENT_IMAGES_BUCKET']

def generate_upload_url(team_id, page_id, file_extension):
    """Generate pre-signed S3 URL for image upload"""
    
    # Generate unique filename
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    key = f"{team_id}/{page_id}/{timestamp}_{unique_id}.{file_extension}"
    
    # Generate pre-signed URL (valid for 5 minutes)
    presigned_url = s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': CONTENT_IMAGES_BUCKET,
            'Key': key,
            'ContentType': f'image/{file_extension}'
        },
        ExpiresIn=300
    )
    
    # Return both upload URL and final public URL
    cloudfront_domain = os.environ['CONTENT_CDN_DOMAIN']
    public_url = f"https://{cloudfront_domain}/{key}"
    
    return {
        'uploadUrl': presigned_url,
        'publicUrl': public_url,
        'key': key
    }

def lambda_handler(event, context):
    """API endpoint: POST /admin/content/image-upload-url"""
    
    # Parse request
    body = json.loads(event['body'])
    team_id = body.get('teamId')
    page_id = body.get('pageId', 'temp')
    file_extension = body.get('fileExtension', 'jpg')
    
    # Validate file extension
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    if file_extension.lower() not in allowed_extensions:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid file type'})
        }
    
    # Generate URLs
    result = generate_upload_url(team_id, page_id, file_extension)
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

### Frontend Image Upload (React)
```javascript
async function uploadImageToS3(file, teamId, pageId) {
  try {
    // Get file extension
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    // Request pre-signed URL from API
    const response = await fetch(`${API_URL}/admin/content/image-upload-url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        teamId,
        pageId,
        fileExtension
      })
    });
    
    const { uploadUrl, publicUrl } = await response.json();
    
    // Upload file directly to S3
    await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type
      }
    });
    
    // Return public URL to insert in editor
    return publicUrl;
    
  } catch (error) {
    console.error('Image upload failed:', error);
    throw error;
  }
}
```

## WYSIWYG Editor Integration

### TinyMCE Configuration (Recommended)
```javascript
import { Editor } from '@tinymce/tinymce-react';

function ContentEditor({ initialContent, onSave }) {
  const [content, setContent] = useState(initialContent);
  
  const editorConfig = {
    height: 500,
    menubar: false,
    plugins: [
      'advlist', 'autolink', 'lists', 'link', 'image', 'charmap',
      'preview', 'anchor', 'searchreplace', 'visualblocks', 'code',
      'fullscreen', 'insertdatetime', 'media', 'table', 'help', 'wordcount'
    ],
    toolbar: 
      'undo redo | formatselect | bold italic underline | \
       alignleft aligncenter alignright | \
       bullist numlist outdent indent | \
       link image media | removeformat | code | help',
    content_style: `
      body { 
        font-family: Inter, sans-serif; 
        font-size: 16px;
        line-height: 1.6;
      }
      h1, h2, h3 { color: #0A1F44; }
      a { color: #00A8E8; }
    `,
    
    // Custom image upload handler
    images_upload_handler: async (blobInfo, progress) => {
      const file = blobInfo.blob();
      const publicUrl = await uploadImageToS3(file, teamId, pageId);
      return publicUrl;
    },
    
    // Paste cleanup
    paste_data_images: true,
    paste_as_text: false,
    paste_preprocess: (plugin, args) => {
      // Remove Word formatting junk
      args.content = args.content.replace(/<\/?span[^>]*>/gi, '');
    }
  };
  
  return (
    <div className="editor-container">
      <Editor
        apiKey="your-tinymce-api-key" // Get free key from TinyMCE
        value={content}
        init={editorConfig}
        onEditorChange={(newContent) => setContent(newContent)}
      />
      
      <div className="editor-actions">
        <button onClick={() => onSave(content, false)}>
          Save Draft
        </button>
        <button onClick={() => onSave(content, true)}>
          Publish
        </button>
      </div>
    </div>
  );
}
```

## Content Page Rendering

### Mobile-Responsive CSS
```css
/* Content page styles */
.content-display {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Inter, -apple-system, system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  color: #1F2937;
}

.content-display h1,
.content-display h2,
.content-display h3,
.content-display h4 {
  color: #0A1F44;
  font-weight: 700;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.content-display h1 { font-size: 2rem; }
.content-display h2 { font-size: 1.75rem; }
.content-display h3 { font-size: 1.5rem; }
.content-display h4 { font-size: 1.25rem; }

.content-display p {
  margin-bottom: 1em;
}

.content-display a {
  color: #00A8E8;
  text-decoration: underline;
}

.content-display img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5em auto;
  border-radius: 8px;
}

.content-display iframe {
  max-width: 100%;
  aspect-ratio: 16 / 9;
  margin: 1.5em auto;
  display: block;
}

.content-display ul,
.content-display ol {
  margin-left: 1.5em;
  margin-bottom: 1em;
}

.content-display li {
  margin-bottom: 0.5em;
}

.content-display table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  overflow-x: auto;
  display: block;
}

.content-display th,
.content-display td {
  padding: 0.75em;
  border: 1px solid #E5E7EB;
  text-align: left;
}

.content-display th {
  background-color: #0A1F44;
  color: white;
  font-weight: 600;
}

/* Mobile optimizations */
@media (max-width: 768px) {
  .content-display {
    padding: 15px;
    font-size: 14px;
  }
  
  .content-display h1 { font-size: 1.75rem; }
  .content-display h2 { font-size: 1.5rem; }
  .content-display h3 { font-size: 1.25rem; }
  
  .content-display table {
    font-size: 0.875rem;
  }
}
```

## Example Content Templates

### Workout Template
```html
<h1>Wall Ball Fundamentals</h1>

<p>Consistent wall ball practice is the foundation of lacrosse stick skills. This 20-minute routine will help you develop muscle memory and improve your throwing and catching technique.</p>

<h2>What You'll Need</h2>
<ul>
  <li>Lacrosse stick and ball</li>
  <li>Wall or rebounder</li>
  <li>Timer</li>
  <li>At least 10 feet of space</li>
</ul>

<h2>The Routine</h2>

<h3>Warm-up (5 minutes)</h3>
<ol>
  <li>Right hand only - 50 throws</li>
  <li>Left hand only - 50 throws</li>
  <li>Alternating hands - 50 throws</li>
</ol>

<h3>Main Work (12 minutes)</h3>
<img src="https://example.com/wall-ball-form.jpg" alt="Proper wall ball form">

<p>Focus on these key points during your main work:</p>
<ul>
  <li><strong>Hand position:</strong> Top hand at the throat, bottom hand at the butt</li>
  <li><strong>Target:</strong> Aim for a spot on the wall at shoulder height</li>
  <li><strong>Follow through:</strong> Point your stick where you want the ball to go</li>
</ul>

<h3>Cool down (3 minutes)</h3>
<p>Finish with some ground ball practice and light stretching.</p>

<h2>Video Tutorial</h2>
<iframe src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0" allowfullscreen></iframe>

<h2>Track Your Progress</h2>
<p>Remember to check off "Daily Wall Ball (20 mins)" in your consistency tracker!</p>
```

### Nutrition Template
```html
<h1>Game Day Nutrition Guide</h1>

<p>What you eat before a game can significantly impact your performance. Follow this guide to fuel your body properly.</p>

<h2>3-4 Hours Before Game</h2>
<p>Eat a balanced meal with:</p>
<ul>
  <li>Complex carbs (pasta, rice, whole grain bread)</li>
  <li>Lean protein (chicken, fish, turkey)</li>
  <li>Vegetables</li>
  <li>Hydration (16-20 oz water)</li>
</ul>

<table>
  <thead>
    <tr>
      <th>Good Choices</th>
      <th>Avoid</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Grilled chicken with brown rice</td>
      <td>Heavy, greasy foods</td>
    </tr>
    <tr>
      <td>Whole wheat pasta with lean meat sauce</td>
      <td>High-fiber foods that cause bloating</td>
    </tr>
    <tr>
      <td>Turkey sandwich on whole grain</td>
      <td>Sugary sodas and candy</td>
    </tr>
  </tbody>
</table>

<h2>1-2 Hours Before Game</h2>
<p>Light snack for energy boost:</p>
<ul>
  <li>Banana with peanut butter</li>
  <li>Sports drink</li>
  <li>Granola bar</li>
</ul>

<h2>During Game</h2>
<p>Stay hydrated! Drink 7-10 oz every 15-20 minutes.</p>

<h2>After Game</h2>
<p>Within 30 minutes, consume protein and carbs to help recovery.</p>
```

## DynamoDB Schema for Content Pages

```python
# Example content page item in DynamoDB
{
    'pageId': 'uuid-here',
    'teamId': 'team-123',
    'slug': 'wall-ball-fundamentals',
    'title': 'Wall Ball Fundamentals',
    'category': 'workouts',
    'htmlContent': '<h1>Wall Ball Fundamentals</h1>...',  # Full sanitized HTML
    'isPublished': True,
    'displayOrder': 1,
    'createdBy': 'coach@example.com',
    'createdAt': '2025-01-15T10:30:00Z',
    'updatedAt': '2025-01-20T14:22:00Z',
    'lastEditedBy': 'assistant-coach@example.com'
}
```

## API Request/Response Examples

### Create Content Page
```json
POST /admin/content
Authorization: Bearer {jwt-token}

Request:
{
  "title": "Wall Ball Fundamentals",
  "category": "workouts",
  "htmlContent": "<h1>Wall Ball Fundamentals</h1>...",
  "isPublished": false,
  "displayOrder": 1
}

Response:
{
  "pageId": "uuid-here",
  "slug": "wall-ball-fundamentals",
  "createdAt": "2025-01-15T10:30:00Z",
  "message": "Content page created successfully"
}
```

### Publish Content Page
```json
PUT /admin/content/{pageId}/publish
Authorization: Bearer {jwt-token}

Request:
{
  "isPublished": true
}

Response:
{
  "pageId": "uuid-here",
  "isPublished": true,
  "publishedAt": "2025-01-15T10:35:00Z",
  "message": "Content published successfully"
}
```

### Get Published Content (Player Access)
```json
GET /content?category=workouts

Response:
{
  "pages": [
    {
      "pageId": "uuid-here",
      "slug": "wall-ball-fundamentals",
      "title": "Wall Ball Fundamentals",
      "category": "workouts",
      "displayOrder": 1
    },
    {
      "pageId": "uuid-2",
      "slug": "stick-skills-drills",
      "title": "Stick Skills Drills",
      "category": "workouts",
      "displayOrder": 2
    }
  ]
}
```

### Get Content Page Detail (Player Access)
```json
GET /content/wall-ball-fundamentals

Response:
{
  "pageId": "uuid-here",
  "title": "Wall Ball Fundamentals",
  "category": "workouts",
  "htmlContent": "<h1>Wall Ball Fundamentals</h1>...",
  "lastUpdated": "2025-01-20T14:22:00Z"
}
```

## Testing Checklist

- [ ] HTML sanitization removes `<script>` tags
- [ ] HTML sanitization removes onclick/onerror handlers
- [ ] Only YouTube/Vimeo iframes allowed
- [ ] Images upload to S3 successfully
- [ ] Pre-signed URLs expire after 5 minutes
- [ ] Content renders correctly on mobile
- [ ] Content renders correctly on desktop
- [ ] Published content visible to players
- [ ] Unpublished content hidden from players
- [ ] Multiple coaches can edit same content
- [ ] Auto-save works in editor
- [ ] Image file size limits enforced (5MB)
- [ ] Invalid file types rejected
- [ ] Content displays in correct category
- [ ] Display order/reordering works
- [ ] Search/filter in admin works
- [ ] Preview mode shows accurate rendering

## Performance Considerations

1. **Content Caching**: Cache rendered HTML content in CloudFront (1 hour TTL)
2. **Image Optimization**: Resize images on upload to max 2000px width
3. **Lazy Loading**: Load content pages on-demand, not all at app start
4. **Content Size**: Limit HTML content to 400KB per page
5. **Image CDN**: Serve all images through CloudFront for fast global delivery

---

This implementation provides a robust, secure content management system that coaches can easily use without technical expertise, while maintaining security best practices and excellent performance.
