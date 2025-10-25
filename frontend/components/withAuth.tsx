import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { Loader2 } from 'lucide-react';

const withAuth = <P extends object>(WrappedComponent: React.ComponentType<P>) => {
  const AuthComponent = (props: P) => {
    const router = useRouter();
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
      // If not authenticated, redirect to login page.
      if (!isAuthenticated) {
        router.replace('/auth/login');
      } else {
        setIsLoading(false);
      }
    }, [isAuthenticated, router]);

    if (isLoading) {
      return (
        <div className="flex min-h-screen w-full items-center justify-center bg-background-dark">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      );
    }

    return <WrappedComponent {...props} />;
  };

  return AuthComponent;
};

export default withAuth;
