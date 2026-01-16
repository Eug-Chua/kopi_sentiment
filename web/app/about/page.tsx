export default function AboutPage() {
    return (
      <main className="container mx-auto p-6 max-w-2xl min-h-screen">
        {/* Header with back link */}
        <div className="mb-12">
          <a
            href="/"
            className="text-gray-500 hover:text-white text-sm transition-colors inline-flex items-center gap-1"
          >
            <span>←</span>
            <span>Back to Dashboard</span>
          </a>
        </div>
  
        {/* Hero section */}
        <div className="mb-">
          <h1 className="text-4xl md:text-5xl font-bold font-[family-name:var(--font-space-mono)] mb-4">
            About
          </h1>
          <p className="text-xl text-gray-400">
            Not analyzing. <span className="text-white">Listening.</span>
          </p>
        </div>
  
        {/* Main content with styled sections */}
        <div className="space-y-12">
          {/* The Problem */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-[2px] bg-red-500"></div>
              <h2 className="text-sm uppercase tracking-wider text-gray-500">The Problem</h2>
            </div>
            <p className="text-gray-300 leading-relaxed text-lg">
              Singaporeans are often characterized as complainers. It's easy to dismiss
              the grievances that surface on forums and social media—to write them off
              as noise, negativity, or the usual grumbling.
            </p>
          </section>
  
          {/* The Insight */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-[2px] bg-amber-500"></div>
              <h2 className="text-sm uppercase tracking-wider text-gray-500">The Insight</h2>
            </div>
            <p className="text-gray-300 leading-relaxed text-lg">
              But beneath every complaint is something worth hearing.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-6">
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <p className="text-white font-medium mb-1">Frustrations</p>
                <p className="text-gray-400 text-sm">reveal unmet needs</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <p className="text-white font-medium mb-1">Fears</p>
                <p className="text-gray-400 text-sm">point to what people value</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                <p className="text-white font-medium mb-1">Aspirations</p>
                <p className="text-gray-400 text-sm">show what they hope for</p>
              </div>
            </div>
          </section>
  
          {/* The Approach */}
          <section>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-[2px] bg-green-500"></div>
              <h2 className="text-sm uppercase tracking-wider text-gray-500">The Approach</h2>
            </div>
            <p className="text-gray-300 leading-relaxed text-lg">
              Kopi Sentiment looks past the surface to understand what Singaporeans are{" "}
              <em className="text-white not-italic">really</em> trying to say. What are they worried
              about? What do they wish was different? What future are they hoping for?
            </p>
          </section>
  
          {/* The Goal */}
          <section className="bg-gradient-to-r from-white/5 to-transparent rounded-xl p-6 border-l-2 border-white/20">
            <p className="text-gray-200 leading-relaxed text-lg">
              The goal isn't to judge or categorize. It's to create space for{" "}
              <span className="text-white font-medium">empathy</span>—to treat online discourse 
              not as data to be mined, but as voices to be heard.
            </p>
          </section>
        </div>
  
        {/* Footer */}
        <footer className="mt-20 pt-8 border-t border-white/10">
          <p className="text-gray-500 text-sm">
            Data sourced from Singapore-related subreddits. Analysis powered by AI
            to identify themes, sentiments, and underlying concerns.
          </p>
        </footer>
      </main>
    );
  }
  