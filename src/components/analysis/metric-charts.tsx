
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

function baseBarOptions(): ChartOptions<"bar"> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.95)",
        titleColor: "#fff",
        bodyColor: "#fff",
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: "#64748b",
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: "rgba(148, 163, 184, 0.16)",
        },
        ticks: {
          color: "#64748b",
        },
      },
    },
  };
}

function baseDoughnutOptions(): ChartOptions<"doughnut"> {
  return {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "72%",
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          usePointStyle: true,
          boxWidth: 10,
        },
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.95)",
        titleColor: "#fff",
        bodyColor: "#fff",
      },
    },
  };
}

export function MetricBarCard({
  title,
  description,
  labels,
  values,
  accent = "rgba(59, 130, 246, 0.85)",
}: {
  title: string;
  description?: string;
  labels: string[];
  values: number[];
  accent?: string;
}) {
  const data: ChartData<"bar"> = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: accent,
        borderRadius: 12,
      },
    ],
  };

  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <Bar data={data} options={baseBarOptions()} />
        </div>
      </CardContent>
    </Card>
  );
}

export function SeverityDoughnutCard({
  title,
  description,
  labels,
  values,
  colors,
}: {
  title: string;
  description?: string;
  labels: string[];
  values: number[];
  colors: string[];
}) {
  const data: ChartData<"doughnut"> = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: colors,
        borderWidth: 0,
      },
    ],
  };

  return (
    <Card className="border-border/70 bg-card/95 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <Doughnut data={data} options={baseDoughnutOptions()} />
        </div>
      </CardContent>
    </Card>
  );
}
