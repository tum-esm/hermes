import { RecoilEnv, atom } from "recoil";

export type ServerStatusObject = {
  environment: string;
  commit_sha: string;
  branch_name: string;
  start_timestamp: number;
};

RecoilEnv.RECOIL_DUPLICATE_ATOM_KEY_CHECKING_ENABLED = false;

export const serverStatusState = atom<ServerStatusObject | null>({
  key: "serverStatusState",
  default: null,
});
