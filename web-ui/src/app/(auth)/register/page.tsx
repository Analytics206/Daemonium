import { Metadata } from 'next';
import RegisterForm from '@/components/auth/register-form';
import AuthLayout from '@/components/auth/auth-layout';

export const metadata: Metadata = {
  title: 'Create Account',
  description: 'Join Daemonium to start meaningful conversations with philosopher personas.',
};

export default function RegisterPage() {
  return (
    <AuthLayout
      title="Join Daemonium"
      subtitle="Create your account to begin exploring philosophical wisdom"
    >
      <RegisterForm />
    </AuthLayout>
  );
}
