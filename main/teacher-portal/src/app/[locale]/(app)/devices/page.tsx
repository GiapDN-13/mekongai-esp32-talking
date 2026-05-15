"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Wifi, Smartphone, CheckCircle2, Loader2, RefreshCw, Cpu, Pencil, Plus } from "lucide-react";
import { toast } from "sonner";
import { backendFetch, getToken } from "@/lib/api";

interface Agent { id: string; agentName: string; }
interface Device { id: string; macAddress: string; alias?: string; board?: string; appVersion?: string; }

export default function DevicesPage() {
  const [tab, setTab] = useState<'manage' | 'setup'>('manage');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [deviceCode, setDeviceCode] = useState('');
  const [isBinding, setIsBinding] = useState(false);
  const [initDone, setInitDone] = useState(false);

  function tk() { return getToken() || ''; }

  async function ensureAgent(): Promise<string | null> {
    try {
      const data = await backendFetch('/agent/list', { token: tk() });
      const list = Array.isArray(data) ? data : [];
      if (list.length > 0) {
        setAgents(list);
        const id = list[0].id;
        setActiveAgent(id);
        return id;
      }
      toast.info("Đang tạo Trợ giảng cho bạn...");
      const newId = await backendFetch('/agent', {
        method: 'POST',
        body: JSON.stringify({ agentName: "Trợ giảng của tôi" }),
        token: tk(),
      });
      const agentId = typeof newId === 'string' ? newId : newId?.id || newId;
      if (agentId) {
        toast.success("Đã tạo Trợ giảng!");
        const refreshed = await backendFetch('/agent/list', { token: tk() });
        setAgents(Array.isArray(refreshed) ? refreshed : []);
        setActiveAgent(agentId);
        return agentId;
      }
      return null;
    } catch (err: any) {
      toast.error("Lỗi: " + err.message);
      return null;
    }
  }

  async function loadDevices(agentId: string) {
    setIsLoading(true);
    try {
      const data = await backendFetch(`/device/bind/${agentId}`, { token: tk() });
      setDevices(Array.isArray(data) ? data : []);
    } catch {
      setDevices([]);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (initDone) return;
    ensureAgent().then(id => {
      if (id) loadDevices(id);
      setInitDone(true);
    });
  }, [initDone]);

  useEffect(() => {
    if (activeAgent && initDone) loadDevices(activeAgent);
  }, [activeAgent]);

  const handleBind = async () => {
    if (!deviceCode.trim()) { toast.error("Nhập mã kích hoạt thiết bị"); return; }
    if (!activeAgent) { toast.error("Chưa có Trợ giảng"); return; }
    setIsBinding(true);
    try {
      await backendFetch(`/device/bind/${activeAgent}/${deviceCode}`, { method: 'POST', token: tk() });
      toast.success("Ghép nối thành công!");
      setDeviceCode('');
      setStep(1);
      setTab('manage');
      await loadDevices(activeAgent);
    } catch (err: any) {
      toast.error("Ghép nối thất bại: " + err.message);
    } finally {
      setIsBinding(false);
    }
  };

  const handleUnbind = async (deviceId: string) => {
    try {
      await backendFetch('/device/unbind', { method: 'POST', body: JSON.stringify({ deviceId }), token: tk() });
      toast.success("Đã huỷ liên kết");
      if (activeAgent) await loadDevices(activeAgent);
    } catch (err: any) { toast.error(err.message); }
  };

  const handleUpdateAlias = async (deviceId: string, alias: string) => {
    try {
      await backendFetch(`/device/update/${deviceId}`, { method: 'PUT', body: JSON.stringify({ alias }), token: tk() });
      toast.success("Đã cập nhật");
      if (activeAgent) await loadDevices(activeAgent);
    } catch (err: any) { toast.error(err.message); }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Cài đặt Robot</h1>
          <p className="text-muted-foreground">Quản lý và ghép nối thiết bị ESP32.</p>
        </div>
        <div className="flex gap-2">
          <Button variant={tab === 'manage' ? 'default' : 'outline'} size="sm" onClick={() => setTab('manage')}>
            <Cpu className="w-4 h-4 mr-2" /> Thiết bị ({devices.length})
          </Button>
          <Button variant={tab === 'setup' ? 'default' : 'outline'} size="sm" onClick={() => setTab('setup')}>
            <Plus className="w-4 h-4 mr-2" /> Ghép nối mới
          </Button>
        </div>
      </div>

      {!initDone ? (
        <div className="text-center p-12"><Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" /></div>
      ) : tab === 'manage' ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Thiết bị đã kết nối</h2>
            <Button variant="outline" size="sm" onClick={() => { if (activeAgent) loadDevices(activeAgent); }}>
              <RefreshCw className="w-4 h-4 mr-2" /> Làm mới
            </Button>
          </div>
          {isLoading ? (
            <div className="text-center p-8"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
          ) : devices.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-8 text-center text-muted-foreground">
                Chưa có thiết bị nào. Nhấn <strong>"Ghép nối mới"</strong> để thêm robot.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {devices.map(d => (
                <Card key={d.id}>
                  <div className="flex items-center p-4 gap-4">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center shrink-0">
                      <Cpu className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium">{d.alias || d.macAddress}</h4>
                      <div className="flex gap-2 mt-1 flex-wrap">
                        <Badge variant="outline" className="text-xs">{d.macAddress}</Badge>
                        {d.board && <Badge variant="outline" className="text-xs">{d.board}</Badge>}
                        {d.appVersion && <Badge variant="outline" className="text-xs">v{d.appVersion}</Badge>}
                      </div>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      <Button variant="ghost" size="icon" title="Đổi tên"
                        onClick={() => { const n = prompt("Tên mới:", d.alias || ''); if (n !== null) handleUpdateAlias(d.id, n); }}>
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="hover:text-destructive" title="Huỷ liên kết"
                        onClick={() => { if (confirm(`Huỷ liên kết ${d.alias || d.macAddress}?`)) handleUnbind(d.id); }}>
                        <Smartphone className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4 relative">
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-muted -z-10"></div>
            <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-primary -z-10 transition-all duration-500" style={{ width: `${(step - 1) * 100}%` }}></div>
            {[1, 2].map(i => (
              <button key={i} onClick={() => { if (i < step) setStep(i); }}
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold border-4 border-background transition-colors ${step >= i ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                {i}
              </button>
            ))}
          </div>

          {step === 1 ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Wifi className="w-5 h-5 text-primary" /> Bước 1: Kết nối Wi-Fi & Lấy mã</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="list-decimal list-inside space-y-2 text-muted-foreground bg-muted/50 p-5 rounded-lg">
                  <li>Cắm điện cho robot. Đèn nhấp nháy xanh.</li>
                  <li>Kết nối điện thoại vào Wi-Fi <strong className="text-foreground">"Robot-TroGiang-..."</strong></li>
                  <li>Nhập Wi-Fi lớp học trên trang cấu hình tự hiện.</li>
                  <li>Robot sẽ đọc <strong className="text-foreground">mã kích hoạt 6 số</strong>. Ghi lại mã này.</li>
                </ol>
              </CardContent>
              <CardFooter className="flex justify-end">
                <Button onClick={() => setStep(2)}>Tôi đã có mã <CheckCircle2 className="w-4 h-4 ml-2" /></Button>
              </CardFooter>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Smartphone className="w-5 h-5 text-primary" /> Bước 2: Nhập mã kích hoạt</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Label>Mã kích hoạt</Label>
                  <Input placeholder="123456" maxLength={6} value={deviceCode} onChange={e => setDeviceCode(e.target.value)}
                    className="text-center text-2xl tracking-widest font-mono" />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setStep(1)}>Quay lại</Button>
                <Button onClick={handleBind} disabled={isBinding}>
                  {isBinding ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                  {isBinding ? "Đang ghép nối..." : "Ghép nối"}
                </Button>
              </CardFooter>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
