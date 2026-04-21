import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useSession } from "@/lib/auth-client";

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refetch } = useSession();

  useEffect(() => {
    const token = searchParams.get("token");
    const isNew = searchParams.get("new") === "true";
    
    if (token) {
      if (typeof window !== "undefined") {
        localStorage.setItem("bearer_token", token);
      }
      refetch();
      
      if (isNew) {
        toast.success("Account created successfully!");
      } else {
        toast.success("Welcome back!");
      }
      
      navigate("/dashboard");
    } else {
      toast.error("Authentication failed. No token received.");
      navigate("/login");
    }
  }, [searchParams, navigate, refetch]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="flex flex-col items-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  );
}
