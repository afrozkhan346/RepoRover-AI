import { useLocation, useNavigate, useSearchParams as useRouterSearchParams } from "react-router-dom";

type NavigateOptions = {
  replace?: boolean;
};

export function useRouter() {
  const navigate = useNavigate();

  return {
    push: (href: string, options?: NavigateOptions) => {
      navigate(href, { replace: options?.replace ?? false });
    },
    replace: (href: string) => {
      navigate(href, { replace: true });
    },
    back: () => {
      navigate(-1);
    },
    forward: () => {
      navigate(1);
    },
    refresh: () => {
      window.location.reload();
    },
    prefetch: async (_href: string) => {
      return;
    },
  };
}

export function usePathname(): string {
  const location = useLocation();
  return location.pathname;
}

export function useSearchParams(): URLSearchParams {
  const [searchParams] = useRouterSearchParams();
  return searchParams;
}