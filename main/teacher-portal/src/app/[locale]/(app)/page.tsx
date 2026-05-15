"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Users, MessageSquare, Cpu } from "lucide-react";
import { backendFetch, getToken } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({ agents: 0, devices: 0, datasets: 0, documents: 0 });

  useEffect(() => {
    async function load() {
      const token = getToken() || '';
      try {
        const [agentData, datasetData] = await Promise.allSettled([
          backendFetch('/agent/list', { token }),
          backendFetch('/datasets?page=1&page_size=50', { token }),
        ]);

        const agents = agentData.status === 'fulfilled' && Array.isArray(agentData.value) ? agentData.value : [];
        const dsRaw = datasetData.status === 'fulfilled' ? datasetData.value : null;
        const datasets = dsRaw?.list || (Array.isArray(dsRaw) ? dsRaw : []);

        let deviceCount = 0;
        let docCount = 0;
        for (const agent of agents) {
          try {
            const devs = await backendFetch(`/device/bind/${agent.id}`, { token });
            deviceCount += Array.isArray(devs) ? devs.length : 0;
          } catch {}
        }
        for (const ds of datasets) {
          docCount += ds.documentCount || ds.document_count || 0;
        }

        setStats({ agents: agents.length, devices: deviceCount, datasets: datasets.length, documents: docCount });
      } catch {}
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Tổng quan</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trợ giảng</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.agents}</div>
            <p className="text-xs text-muted-foreground">Agent đã tạo</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Thiết bị</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.devices}</div>
            <p className="text-xs text-muted-foreground">Robot đã kết nối</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Kho tài liệu</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.datasets}</div>
            <p className="text-xs text-muted-foreground">Knowledge Base</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tài liệu</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.documents}</div>
            <p className="text-xs text-muted-foreground">File đã upload</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
