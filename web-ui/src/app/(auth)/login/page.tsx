import { Metadata } from 'next';
import LoginForm from '../../../components/auth/login-form';
import AuthLayout from '../../../components/auth/auth-layout';

export const metadata: Metadata = {
  title: 'Login',
  description: 'Sign in to your Daemonium account to continue your philosophical journey.',
};

export default function LoginPage() {
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue your philosophical conversations"
    >
      <LoginForm />
    </AuthLayout>
  );
}
