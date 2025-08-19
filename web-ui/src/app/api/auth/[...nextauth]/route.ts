// DEPRECATED ROUTE: NextAuth has been removed in favor of Firebase Authentication.
// This endpoint intentionally returns 410 Gone to signal deprecation and provide guidance.
// See docs: docs/12-release_notes.md and docs/06-system_design.md

export async function GET() {
  return new Response(
    JSON.stringify({
      status: 410,
      error: 'Gone',
      message:
        'NextAuth route has been deprecated. Please use Firebase Authentication. See web-ui/src/lib/firebase.ts and FirebaseAuthProvider.',
      docs: [
        '/docs/12-release_notes.md#web-ui-firebase-authentication-google-sign-in',
        '/docs/06-system_design.md#web-ui-authentication-firebase'
      ],
    }),
    { status: 410, headers: { 'content-type': 'application/json' } }
  );
}

export async function POST() {
  return GET();
}
