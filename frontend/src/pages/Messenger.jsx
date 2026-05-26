import SecureMessengerWidget from '../components/messenger/SecureMessengerWidget';

export default function Messenger() {
  return (
    <div className="h-full bg-slate-100">
      <SecureMessengerWidget standalone />
    </div>
  );
}
