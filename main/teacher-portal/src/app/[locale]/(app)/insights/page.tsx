"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Brain, MessageCircle, Loader2, RefreshCw, ChevronLeft } from "lucide-react";
import { backendFetch, getToken } from "@/lib/api";
import { toast } from "sonner";

interface Agent { id: string; agentName: string; }
interface Session { sessionId: string; createDate: string; }
interface ChatMessage { id: string; chatType: number; content: string; createDate: string; }

export default function InsightsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const tokenRef = useRef(getToken());

  function tk() { return getToken() || ''; }

  async function doLoadAgents() {
    try {
      const data = await backendFetch('/agent/list', { token: tk() });
      const list = Array.isArray(data) ? data : [];
      setAgents(list);
      if (list.length > 0) setActiveAgent(prev => prev || list[0].id);
    } catch (err: any) {
      toast.error("Lỗi: " + err.message);
    }
  }

  async function doLoadSessions(agentId: string) {
    setIsLoading(true);
    try {
      const data = await backendFetch(`/agent/${agentId}/sessions?page=1&limit=30`, { token: tk() });
      setSessions(data?.list || []);
    } catch (err: any) {
      toast.error("Lỗi tải phiên chat: " + err.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function doLoadMessages(agentId: string, sessionId: string) {
    setIsLoading(true);
    try {
      const data = await backendFetch(`/agent/${agentId}/chat-history/${sessionId}`, { token: tk() });
      setMessages(Array.isArray(data) ? data : []);
    } catch (err: any) {
      toast.error("Lỗi tải tin nhắn: " + err.message);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { doLoadAgents(); }, []);
  useEffect(() => { if (activeAgent) { doLoadSessions(activeAgent); setActiveSession(null); setMessages([]); } }, [activeAgent]);
  useEffect(() => { if (activeAgent && activeSession) doLoadMessages(activeAgent, activeSession); }, [activeAgent, activeSession]);

  const totalMessages = messages.length;
  const userMessages = messages.filter(m => m.chatType === 1).length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Lịch sử & Phân tích</h1>
          <p className="text-muted-foreground">Theo dõi các phiên trò chuyện giữa học sinh và robot.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => { if (activeAgent) doLoadSessions(activeAgent); }}>
          <RefreshCw className="w-4 h-4 mr-2" /> Làm mới
        </Button>
      </div>

      {agents.length > 1 && (
        <div className="flex gap-2 flex-wrap">
          {agents.map(a => (
            <Button key={a.id} variant={activeAgent === a.id ? "default" : "outline"} size="sm"
              onClick={() => { setActiveAgent(a.id); setActiveSession(null); }}>
              {a.agentName}
            </Button>
          ))}
        </div>
      )}

      {!activeSession ? (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Các phiên trò chuyện ({sessions.length})</h2>
          {isLoading ? (
            <div className="text-center p-8"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
          ) : sessions.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-8 text-center text-muted-foreground">
                Chưa có phiên trò chuyện nào. Khi học sinh bắt đầu nói chuyện với robot, lịch sử sẽ hiện ở đây.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {sessions.map(s => (
                <Card key={s.sessionId} className="cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => setActiveSession(s.sessionId)}>
                  <div className="flex items-center p-4 gap-4">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center shrink-0">
                      <MessageCircle className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">Phiên #{s.sessionId.slice(-6)}</h4>
                      <p className="text-xs text-muted-foreground">{new Date(s.createDate).toLocaleString('vi-VN')}</p>
                    </div>
                    <Badge variant="outline">Xem chi tiết</Badge>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={() => { setActiveSession(null); setMessages([]); }}>
              <ChevronLeft className="w-4 h-4 mr-1" /> Quay lại
            </Button>
            <h2 className="text-xl font-semibold">Phiên #{activeSession.slice(-6)}</h2>
            <Badge variant="outline">{userMessages} câu hỏi / {totalMessages} tin nhắn</Badge>
          </div>

          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="text-center p-8"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
              ) : messages.length === 0 ? (
                <div className="text-center p-8 text-muted-foreground">Phiên này chưa có tin nhắn.</div>
              ) : (
                <ScrollArea className="h-[600px] p-4">
                  <div className="space-y-4">
                    {messages.map(msg => (
                      <div key={msg.id} className={`flex items-start gap-3 ${msg.chatType === 2 ? 'pl-8' : ''}`}>
                        <Avatar className="w-8 h-8 mt-0.5">
                          <AvatarFallback className={msg.chatType === 1 ? "bg-primary/10 text-primary text-xs" : "bg-blue-100 text-blue-700 text-xs"}>
                            {msg.chatType === 1 ? 'HS' : 'RB'}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className={`font-medium text-sm ${msg.chatType === 2 ? 'text-blue-700' : ''}`}>
                              {msg.chatType === 1 ? 'Học sinh' : 'Trợ giảng'}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(msg.createDate).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className={`text-sm p-3 rounded-md rounded-tl-none inline-block ${msg.chatType === 1 ? 'bg-muted/50' : 'bg-blue-50 text-blue-900'}`}>
                            {msg.content}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
