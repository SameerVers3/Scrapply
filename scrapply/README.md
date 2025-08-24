# Scrapply Frontend

A modern Next.js frontend for the Scrapply AI-powered web scraping platform.

## Features

- **Dashboard**: Create scraping requests and manage jobs
- **Chatbot Interface**: Natural language commands for job management
- **Real-time Updates**: Automatic job status polling
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, intuitive interface built with Tailwind CSS

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend server running (default: http://localhost:8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables (optional):
```bash
# Create .env.local file
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with sidebar and chatbot
│   ├── page.tsx           # Dashboard page
│   ├── chatbot/           # Chatbot standalone page
│   └── settings/          # Settings page
├── components/            # React components
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── ScrapingForm.tsx   # Create scraping request form
│   ├── JobCard.tsx        # Individual job display
│   ├── JobList.tsx        # Job list wrapper
│   ├── Chatbot.tsx        # Chat interface
│   └── ProgressBar.tsx    # Progress indicator
└── lib/                   # Utility functions
    ├── api.ts             # API helper functions
    ├── chatbot.ts         # Chatbot command parsing
    └── utils.ts           # General utilities
```

## Usage

### Dashboard
- Create new scraping requests by entering a URL and description
- View all jobs with real-time status updates
- Test and execute generated APIs
- Retry failed jobs or delete completed ones

### Chatbot Commands
- `"Create scraper for https://example.com"` - Create a new job
- `"List jobs"` - Show all jobs
- `"List ready jobs"` - Show only completed jobs
- `"Delete job [ID]"` - Delete a specific job
- `"Retry job [ID]"` - Retry a failed job
- `"Help"` - Show available commands

### Settings
- Configure API base URL
- Set auto-refresh intervals
- Enable/disable notifications

## API Integration

The frontend communicates with the backend through REST API calls:

- `POST /api/v1/scraping/requests` - Create scraping job
- `GET /api/v1/scraping/jobs` - List jobs
- `GET /api/v1/scraping/jobs/{id}` - Get job status
- `DELETE /api/v1/scraping/jobs/{id}` - Delete job
- `POST /api/v1/scraping/jobs/{id}/retry` - Retry job
- `POST /generated/{id}/test` - Test generated API
- `GET /generated/{id}` - Execute generated API

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Technologies Used

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **clsx** - Conditional class names

## Deployment

The frontend can be deployed to any platform that supports Next.js:

- **Vercel** (recommended)
- **Netlify**
- **Railway**
- **Docker**

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Scrapply platform.
