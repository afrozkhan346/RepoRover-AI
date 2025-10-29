"use client"

interface DashboardCardsProps {
  data: any
}

export default function DashboardCards({ data }: DashboardCardsProps) {
  const cards = [
    { label: "Languages", value: data.languages?.length || 0, icon: "📊" },
    { label: "Files", value: data.fileCount || 0, icon: "📁" },
    { label: "Projects", value: data.projects?.length || 0, icon: "🚀" },
    { label: "Last Analyzed", value: "Just now", icon: "⏱️" },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {cards.map((card, idx) => (
        <div key={idx} className="glass p-6 rounded-lg">
          <div className="text-2xl mb-2">{card.icon}</div>
          <p className="text-sm text-muted-foreground mb-1">{card.label}</p>
          <p className="text-2xl font-bold">{card.value}</p>
        </div>
      ))}
    </div>
  )
}
