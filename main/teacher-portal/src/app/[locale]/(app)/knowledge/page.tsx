"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { UploadCloud, FileText, CheckCircle2, Loader2, Trash2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { backendFetch, getToken } from "@/lib/api";

interface KnowledgeFile {
  id: string;
  documentId: string;
  name: string;
  fileSize: number;
  status: string;
  progress: number;
  createDate: string;
}

export default function KnowledgePage() {
  const [isDragging, setIsDragging] = useState(false);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [initDone, setInitDone] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function tk() { return getToken() || ''; }

  async function fetchFiles(dsId: string) {
    setIsLoadingFiles(true);
    try {
      const data = await backendFetch(`/datasets/${dsId}/documents?page=1&page_size=100`, { token: tk() });
      setFiles(data?.list || data || []);
    } catch {
      setFiles([]);
    } finally {
      setIsLoadingFiles(false);
    }
  }

  useEffect(() => {
    if (initDone) return;
    let cancelled = false;

    async function init() {
      const tkVal = tk();
      try {
        const data = await backendFetch('/datasets?page=1&page_size=50', { token: tkVal });
        if (cancelled) return;
        const list = data?.list || data || [];

        let dsId: string | null = null;
        if (list.length > 0) {
          dsId = list[0].datasetId || list[0].id;
        } else {
          toast.info("Đang tạo kho tài liệu cho bạn...");
          const created = await backendFetch('/datasets', {
            method: 'POST',
            body: JSON.stringify({ name: "Tài liệu bài giảng", description: "Kho tài liệu bài giảng của giáo viên" }),
            token: tkVal,
          });
          if (cancelled) return;
          dsId = created?.datasetId || created?.id || null;
          if (dsId) toast.success("Đã tạo kho tài liệu!");
        }

        if (dsId) {
          setDatasetId(dsId);
          await fetchFiles(dsId);
        }
      } catch (err: any) {
        if (!cancelled) toast.error("Lỗi khởi tạo: " + err.message);
      } finally {
        if (!cancelled) setInitDone(true);
      }
    }

    init();
    return () => { cancelled = true; };
  }, [initDone]);

  const handleRefresh = () => { if (datasetId) fetchFiles(datasetId); };

  const uploadFile = async (file: File) => {
    if (!datasetId) { toast.error("Kho tài liệu chưa sẵn sàng"); return; }
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await backendFetch(`/datasets/${datasetId}/documents`, {
        method: 'POST',
        body: formData,
        token: tk(),
        headers: {},
      });
      toast.success(`Đã tải lên: ${file.name}`);
      await fetchFiles(datasetId);
    } catch (err: any) {
      toast.error("Upload thất bại: " + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    Array.from(e.dataTransfer.files).forEach(uploadFile);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) Array.from(e.target.files).forEach(uploadFile);
    e.target.value = '';
  };

  const handleDelete = async (docId: string, name: string) => {
    if (!datasetId) return;
    try {
      await backendFetch(`/datasets/${datasetId}/documents/${docId}`, { method: 'DELETE', token: tk() });
      toast.success(`Đã xoá: ${name}`);
      await fetchFiles(datasetId);
    } catch (err: any) {
      toast.error("Xoá thất bại: " + err.message);
    }
  };

  const handleParse = async (docId: string) => {
    if (!datasetId) return;
    try {
      await backendFetch(`/datasets/${datasetId}/chunks`, {
        method: 'POST',
        body: JSON.stringify({ document_ids: [docId] }),
        token: tk(),
      });
      toast.info("Đang xử lý tài liệu...");
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        await fetchFiles(datasetId);
        if (attempts > 20) clearInterval(poll);
      }, 3000);
    } catch (err: any) {
      toast.error("Xử lý thất bại: " + err.message);
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusInfo = (status: string) => {
    switch (status) {
      case "0": return { label: "Chờ xử lý", color: "bg-amber-100 text-amber-700", icon: <FileText className="w-5 h-5 text-amber-500" />, actionable: true };
      case "1": return { label: "Robot đang đọc...", color: "bg-blue-100 text-blue-700", icon: <Loader2 className="w-5 h-5 animate-spin text-blue-600" />, actionable: false };
      case "2": return { label: "Đã học xong", color: "bg-green-100 text-green-700", icon: <CheckCircle2 className="w-5 h-5 text-green-600" />, actionable: false };
      case "3": return { label: "Lỗi xử lý", color: "bg-red-100 text-red-700", icon: <FileText className="w-5 h-5 text-red-600" />, actionable: true };
      default: return { label: status || "Không rõ", color: "bg-gray-100 text-gray-700", icon: <FileText className="w-5 h-5" />, actionable: false };
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Bài giảng & Tài liệu</h1>
          <p className="text-muted-foreground">Tải lên tài liệu để robot học và hỗ trợ trả lời câu hỏi của học sinh.</p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="w-4 h-4 mr-2" /> Làm mới
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tải lên tài liệu mới</CardTitle>
          <CardDescription>Hỗ trợ PDF, Word (.docx), Text (.txt). Robot sẽ tự động đọc và học.</CardDescription>
        </CardHeader>
        <CardContent>
          <input ref={fileInputRef} type="file" className="hidden" accept=".pdf,.doc,.docx,.txt" multiple onChange={handleFileSelect} />
          <div
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"}`}
            onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <div className="flex flex-col items-center space-y-4 pointer-events-none">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                {isUploading ? <Loader2 className="w-8 h-8 text-primary animate-spin" /> : <UploadCloud className="w-8 h-8 text-primary" />}
              </div>
              <div className="space-y-1">
                <h3 className="font-medium text-lg">{isUploading ? "Đang tải lên..." : "Kéo thả file vào đây"}</h3>
                <p className="text-sm text-muted-foreground">hoặc click để chọn file từ máy tính</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Tài liệu đã tải ({files.length})</h2>
        {!initDone || (isLoadingFiles && files.length === 0) ? (
          <div className="text-center p-8"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
        ) : files.length === 0 ? (
          <div className="text-center p-8 text-muted-foreground border rounded-lg bg-muted/20">
            Chưa có tài liệu nào. Hãy tải lên bài giảng đầu tiên!
          </div>
        ) : (
          <div className="grid gap-3">
            {files.map(file => {
              const si = getStatusInfo(file.status);
              return (
                <Card key={file.id || file.documentId}>
                  <div className="flex items-center p-4 gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${si.color.split(' ')[0]}`}>
                      {si.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium truncate pr-4">{file.name}</h4>
                        <div className="flex items-center gap-2 shrink-0 text-xs text-muted-foreground">
                          {file.fileSize > 0 && <span>{formatSize(file.fileSize)}</span>}
                          {file.createDate && <span>{new Date(file.createDate).toLocaleDateString('vi-VN')}</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={si.color + " border-none"}>{si.label}</Badge>
                        {file.status === "2" && <span className="text-xs text-muted-foreground">Robot đã sẵn sàng trả lời câu hỏi về bài này</span>}
                      </div>
                      {file.status === "1" && file.progress > 0 && <Progress value={file.progress} className="h-1.5 mt-2" />}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {si.actionable && (
                        <Button variant="outline" size="sm" onClick={() => handleParse(file.documentId || file.id)}>
                          <RefreshCw className="w-3 h-3 mr-1" /> Xử lý
                        </Button>
                      )}
                      <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-destructive"
                        onClick={() => handleDelete(file.documentId || file.id, file.name)} title="Xoá">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
